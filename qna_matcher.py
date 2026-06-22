import json
import subprocess
import numpy as np
import os
import traceback


QA_PATH = "data/qa_pairs.json"
TOOLS_PATH = "data/tools.json"
CACHE_PATH = "data/qa_index_cache.npz"

SIMILARITY_THRESHOLD = 0.45


def load_json(path):
    with open(path, "r") as f:
        return json.load(f)


def get_embedding(text):
    cmd = ["python3", "-m", "embeddings.minilm", text]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("\n[EMBEDDING ERROR]")
        print("Command:", " ".join(cmd))
        print("Return code:", result.returncode)
        print("\nSTDOUT:")
        print(result.stdout)
        print("\nSTDERR:")
        print(result.stderr)
        raise RuntimeError("Embedding command failed")

    output = result.stdout.strip()

    start = output.find("[")
    end = output.rfind("]")

    if start == -1 or end == -1 or end <= start:
        print("\n[PARSE ERROR]")
        print("Could not find embedding vector brackets.")
        print("Full output:")
        print(output)
        raise ValueError("Could not parse embedding output")

    vector_text = output[start + 1:end]
    vector_text = vector_text.replace(",", " ")

    values = []

    for item in vector_text.split():
        try:
            values.append(float(item))
        except ValueError:
            pass

    if len(values) == 0:
        print("\n[PARSE ERROR]")
        print("Found brackets, but no numbers were parsed.")
        print("Vector text:")
        print(vector_text[:1000])
        raise ValueError("Could not parse embedding numbers")

    return np.array(values, dtype=np.float32)


def cosine_similarity(a, b):
    a_norm = np.linalg.norm(a)
    b_norm = np.linalg.norm(b)

    if a_norm == 0 or b_norm == 0:
        return 0.0

    return float(np.dot(a, b) / (a_norm * b_norm))


def qa_signature(qa_pairs):
    """
    Creates a stable string from qa_pairs.json.
    If qa_pairs.json changes, the cache becomes invalid.
    """
    return json.dumps(qa_pairs, sort_keys=True)


def save_index_cache(qa_pairs, index):
    questions = []
    answers = []
    embeddings = []

    for item in index:
        questions.append(item["question"])
        answers.append(item["answer"])
        embeddings.append(item["embedding"])

    np.savez(
        CACHE_PATH,
        signature=qa_signature(qa_pairs),
        questions=np.array(questions),
        answers=np.array(answers),
        embeddings=np.array(embeddings, dtype=np.float32)
    )

    print("Saved QnA index cache:", CACHE_PATH)


def load_index_cache(qa_pairs):
    if not os.path.exists(CACHE_PATH):
        return None

    try:
        cache = np.load(CACHE_PATH, allow_pickle=True)

        cached_signature = str(cache["signature"])
        current_signature = qa_signature(qa_pairs)

        if cached_signature != current_signature:
            print("QnA file changed. Rebuilding embedding index...")
            return None

        questions = cache["questions"]
        answers = cache["answers"]
        embeddings = cache["embeddings"]

        index = []

        for i in range(len(questions)):
            index.append({
                "question": str(questions[i]),
                "answer": str(answers[i]),
                "embedding": embeddings[i]
            })

        print("Loaded QnA index from cache.")
        return index

    except Exception:
        print("[CACHE ERROR] Could not load cache. Rebuilding index...")
        traceback.print_exc()
        return None


def build_index(qa_pairs):
    cached_index = load_index_cache(qa_pairs)

    if cached_index is not None:
        return cached_index

    print("Building QnA embedding index...")

    index = []

    for item in qa_pairs:
        question = item["question"]
        answer = item["answer"]

        embedding = get_embedding(question)

        index.append({
            "question": question,
            "answer": answer,
            "embedding": embedding
        })

        print("Indexed:", question, "->", answer)

    print("Done building index.")

    save_index_cache(qa_pairs, index)

    return index


def find_best_match(user_text, index):
    query_embedding = get_embedding(user_text)

    best_item = None
    best_score = -1.0

    for item in index:
        score = cosine_similarity(query_embedding, item["embedding"])

        if score > best_score:
            best_score = score
            best_item = item

    if best_item is None:
        return {
            "matched": False,
            "user_text": user_text,
            "best_question": None,
            "answer": "{unknown}",
            "score": 0.0
        }

    if best_score < SIMILARITY_THRESHOLD:
        return {
            "matched": False,
            "user_text": user_text,
            "best_question": best_item["question"],
            "answer": "{unknown}",
            "score": best_score
        }

    return {
        "matched": True,
        "user_text": user_text,
        "best_question": best_item["question"],
        "answer": best_item["answer"],
        "score": best_score
    }


def run_tool_for_answer(answer, tools):
    for tool in tools:
        if tool["token"] == answer:
            command = tool["command"]

            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True
            )

            if result.returncode != 0:
                print("\n[TOOL ERROR]")
                print("Command:", command)
                print("Return code:", result.returncode)
                print("\nSTDOUT:")
                print(result.stdout)
                print("\nSTDERR:")
                print(result.stderr)
                return "TOOL_ERROR"

            return result.stdout.strip()

    return "NO_TOOL_FOUND"


class QnAMatcher:
    def __init__(self):
        self.qa_pairs = load_json(QA_PATH)
        self.tools = load_json(TOOLS_PATH)
        self.index = build_index(self.qa_pairs)

    def match(self, user_text):
        return find_best_match(user_text, self.index)

    def match_and_run(self, user_text):
        try:
            match = self.match(user_text)

            print("User text:", match["user_text"])
            print("Best QnA question:", match["best_question"])
            print("Similarity:", round(match["score"], 3))
            print("Answer token:", match["answer"])

            if not match["matched"]:
                print("Rejected: command not confident enough.")
                return {
                    "matched": False,
                    "action_output": "UNKNOWN_COMMAND",
                    "match": match
                }

            action_output = run_tool_for_answer(match["answer"], self.tools)

            return {
                "matched": True,
                "action_output": action_output,
                "match": match
            }

        except Exception:
            print("\n[QNA ERROR] Matching failed, but program will continue.")
            traceback.print_exc()

            return {
                "matched": False,
                "action_output": "QNA_ERROR",
                "match": {
                    "matched": False,
                    "user_text": user_text,
                    "best_question": None,
                    "answer": "{error}",
                    "score": 0.0
                }
            }


if __name__ == "__main__":
    matcher = QnAMatcher()

    while True:
        text = input("\nCommand text: ")

        if text.lower() in ["exit", "quit"]:
            break

        result = matcher.match_and_run(text)

        print("Matched:", result["matched"])
        print("Action output:", result["action_output"])
