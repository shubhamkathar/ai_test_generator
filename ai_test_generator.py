import ast
import subprocess
from pathlib import Path
from google import genai


client = genai.Client(api_key="YOUR_API_KEY_HERE")


def analyze_code(source_code: str):
    tree = ast.parse(source_code)

    analysis = {
        "functions": [],
        "classes": []
    }

    for node in ast.walk(tree):

        # Functions
        if isinstance(node, ast.FunctionDef):
            analysis["functions"].append({
                "name": node.name,
                "args": [arg.arg for arg in node.args.args],
                "lines": getattr(node, "end_lineno", None)
            })

        # Classes
        if isinstance(node, ast.ClassDef):
            analysis["classes"].append(node.name)

    return analysis



def generate_test_cases(code, analysis):
    prompt = f"""
You are a senior QA engineer.

Based on the following Python code structure:
{analysis}

Generate test cases covering:
- Happy path
- Boundary values
- Null/None inputs
- Invalid inputs
- Exception cases
- Edge cases

Return ONLY structured test cases in short format.

CODE:
{code}
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text


def generate_unit_tests(code, test_cases):
    prompt = f"""
You are a Python testing expert.

Generate ONLY executable pytest unit test code.

Rules:
- Use pytest
- Cover all test cases below
- No explanation
- No markdown
- Code must run directly

TEST CASES:
{test_cases}

CODE:
{code}
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text


def save_tests(test_code: str, filename="test_generated.py"):
    Path(filename).write_text(test_code, encoding="utf-8")
    return filename



def run_tests():
    result = subprocess.run(
        ["pytest", "-q"],
        capture_output=True,
        text=True
    )

    return {
        "output": result.stdout,
        "errors": result.stderr
    }


def improve_tests(code, failure_logs):
    prompt = f"""
Fix and improve pytest test cases.

Errors:
{failure_logs}

Original Code:
{code}

Return ONLY corrected pytest code.
"""

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=prompt
    )

    return response.text



def process_file(file_path: str):
    code = Path(file_path).read_text(encoding="utf-8")

    print("\n📊 Running AST Analysis...")
    analysis = analyze_code(code)
    print(analysis)

    print("\n🧪 Generating Test Cases...")
    test_cases = generate_test_cases(code, analysis)
    print(test_cases)

    print("\n⚙️ Generating Unit Tests...")
    test_code = generate_unit_tests(code, test_cases)

    test_file = save_tests(test_code)
    print(f"\n✅ Tests saved to {test_file}")

    print("\n🚀 Running Tests...")
    result = run_tests()

    print("\n📄 Test Output:")
    print(result["output"])

 
    if result["errors"]:
        print("\n🔁 Improving tests using AI feedback loop...")

        improved = improve_tests(code, result["errors"])
        save_tests(improved)

        print("\n🚀 Re-running improved tests...")
        result = run_tests()
        print(result["output"])



# MAIN 

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ai_test_generator.py <file.py>")
        exit()

    process_file(sys.argv[1])
