"""Schema-constrained labeling with any chat-completion model (Anthropic, or an OpenAI-compatible
endpoint such as vLLM, Together, DeepInfra, Fireworks, OpenRouter for open-weight models).

Every pipeline calls `label_records(records, prompt_path, schema_path, ...)`, which sends one record
per request, asks for a JSON object that validates against the pipeline's schema, caches results on
disk by (model, prompt, schema, text) so re-runs are free, and writes JSONL with the model and prompt
version in every row.

Usage from the repository root:

    # closed model (default; needs ANTHROPIC_API_KEY)
    python 2_label/llm.py --prompt 2_label/prompts/label_citation_function.md --schema 2_label/schema.json \
        --input data/0_raw/pilot/citation_windows_raw.jsonl --output data/3_validate/relabeled_claude.jsonl

    # open-weight model on an OpenAI-compatible endpoint (needs OPENAI_API_KEY or --api-key)
    python 2_label/llm.py --provider openai --base-url https://api.together.xyz/v1 \
        --model Qwen/Qwen3.6-32B-Instruct --prompt 2_label/prompts/label_citation_function.md --schema 2_label/schema.json \
        --input data/0_raw/pilot/citation_windows_raw.jsonl --output data/3_validate/relabeled_qwen.jsonl

    # local vLLM server
    python 2_label/llm.py --provider openai --base-url http://localhost:8000/v1 --model Qwen/Qwen3.6-32B-Instruct ...

Then: python 3_validate/validate.py agreement --a data/2_label/pilot/citation_windows_labeled.jsonl --b data/3_validate/relabeled_qwen.jsonl \
          --id window_id --field function
"""
import argparse, hashlib, json, os, pathlib, sys, time

DEFAULT_MODEL = os.environ.get("CSS_MODEL", "claude-fable-5-1")
DEFAULT_PROVIDER = os.environ.get("CSS_PROVIDER", "anthropic")


class Chat:
    """Minimal provider-agnostic chat call: returns the assistant text for (system, user)."""

    def __init__(self, provider=DEFAULT_PROVIDER, model=DEFAULT_MODEL, base_url=None, api_key=None, temperature=0.0, max_tokens=800):
        self.provider, self.model, self.temperature, self.max_tokens = provider, model, temperature, max_tokens
        if provider == "anthropic":
            try:
                import anthropic
            except ImportError:
                sys.exit("pip install anthropic")
            self.client = anthropic.Anthropic(api_key=api_key) if api_key else anthropic.Anthropic()
        elif provider == "openai":
            try:
                import openai
            except ImportError:
                sys.exit("pip install openai")
            self.client = openai.OpenAI(base_url=base_url, api_key=api_key or os.environ.get("OPENAI_API_KEY", "EMPTY"))
        else:
            sys.exit(f"unknown provider {provider!r}; use anthropic or openai")

    def __call__(self, system, user):
        if self.provider == "anthropic":
            msg = self.client.messages.create(model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
                                              system=system, messages=[{"role": "user", "content": user}])
            return msg.content[0].text
        resp = self.client.chat.completions.create(model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
                                                   messages=[{"role": "system", "content": system}, {"role": "user", "content": user}])
        return resp.choices[0].message.content or ""


def _cache_key(model, prompt, schema, record_text):
    h = hashlib.sha256()
    for part in (model, prompt, json.dumps(schema, sort_keys=True), record_text):
        h.update(part.encode("utf-8"))
    return h.hexdigest()


def label_one(chat, prompt, schema, record_text, max_retries=4):
    """Return a dict validating against `schema` (enums enforced; full validation is in validate.py)."""
    system = (
        "You label text for an economics-of-innovation dataset. Follow the labeling guide exactly. "
        "Answer with one JSON object and nothing else. The object must use only these keys: "
        + ", ".join(schema["properties"].keys())
        + ". For enumerated fields use only the listed values. Quote supporting text verbatim where the guide asks for a quote; never invent facts not in the text."
    )
    user = prompt + "\n\n---\nTEXT TO LABEL:\n" + record_text + "\n---\nJSON:"
    for attempt in range(max_retries):
        try:
            txt = chat(system, user).strip()
            txt = txt[txt.find("{"): txt.rfind("}") + 1]
            obj = json.loads(txt)
            for k, spec in schema["properties"].items():
                if "enum" in spec and obj.get(k) not in spec["enum"]:
                    raise ValueError(f"{k}={obj.get(k)!r} not in enum")
            return obj
        except Exception as e:  # noqa: BLE001
            if attempt == max_retries - 1:
                return {"_error": str(e)}
            time.sleep(2 ** attempt)


def label_records(records, prompt_path, schema_path, output_path, text_field="text", model=DEFAULT_MODEL,
                  provider=DEFAULT_PROVIDER, base_url=None, api_key=None, cache_dir=".llm_cache", workers=1, max_tokens=800):
    """Label every record (cached by model, prompt, schema and text); `workers` > 1 sends requests concurrently
    (a vLLM server batches them); the output keeps the input order."""
    from concurrent.futures import ThreadPoolExecutor
    prompt = pathlib.Path(prompt_path).read_text(encoding="utf-8")
    schema = json.loads(pathlib.Path(schema_path).read_text(encoding="utf-8"))
    cache = pathlib.Path(cache_dir); cache.mkdir(exist_ok=True)
    chat = Chat(provider=provider, model=model, base_url=base_url, api_key=api_key, max_tokens=max_tokens)
    prompt_version = hashlib.sha256(prompt.encode()).hexdigest()[:10]
    n_hit = n_err = 0

    def one(rec):
        text = rec[text_field] if isinstance(rec[text_field], str) else json.dumps(rec[text_field], ensure_ascii=False)
        cpath = cache / f"{_cache_key(model, prompt, schema, text)}.json"
        if cpath.exists():
            return json.loads(cpath.read_text(encoding="utf-8")), True
        obj = label_one(chat, prompt, schema, text)
        if "_error" not in obj:
            cpath.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
        return obj, False

    with open(output_path, "w", encoding="utf-8") as out, ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for rec, (obj, hit) in zip(records, pool.map(one, records)):
            n_hit += hit; n_err += "_error" in obj
            row = dict(rec); row.update(obj); row["_model"] = model; row["_provider"] = provider; row["_prompt_version"] = prompt_version
            out.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"labeled {len(records)} records ({n_hit} from cache, {n_err} errors) -> {output_path}")


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--prompt", required=True); ap.add_argument("--schema", required=True)
    ap.add_argument("--input", required=True); ap.add_argument("--output", required=True)
    ap.add_argument("--text-field", default="text"); ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--provider", default=DEFAULT_PROVIDER, choices=["anthropic", "openai"])
    ap.add_argument("--base-url", default=None, help="OpenAI-compatible endpoint, e.g. http://localhost:8000/v1 (vLLM) or https://api.together.xyz/v1")
    ap.add_argument("--api-key", default=None)
    ap.add_argument("--max-tokens", type=int, default=800, help="completion budget; raise for models that think before the JSON")
    ap.add_argument("--workers", type=int, default=1, help="concurrent requests (e.g. 32 against a local vLLM server)")
    ap.add_argument("--limit", type=int, default=0)
    a = ap.parse_args()
    recs = [json.loads(l) for l in open(a.input, encoding="utf-8")]
    if a.limit:
        recs = recs[: a.limit]
    label_records(recs, a.prompt, a.schema, a.output, text_field=a.text_field, model=a.model, workers=a.workers, max_tokens=a.max_tokens,
                  provider=a.provider, base_url=a.base_url, api_key=a.api_key)
