#!/usr/bin/env python3
"""
Benchmark Qwen 2.5 32B para uso Multi-Agente
Prueba: Contexto, Coding, Razonamiento, Following Instructions
"""

import subprocess
import time
import json

MODEL = "qwen2.5:32b"

TESTS = [
    {
        "name": "Context Retention",
        "prompt": """You are Agent Coordinator in a multi-agent system.

Context from previous agents:
- Research Agent found: "Aurora Alpha is a reasoning model launched Feb 8 2026, free on OpenRouter, made by 'Stealth'"
- API Agent confirmed: "Endpoint /api/chat exists, requires Bearer token, rate limit 60 RPM"
- Planner Agent decided: "Use Aurora for reasoning tasks, fallback to Claude for code"

Based on this context, what model should I use for a task that requires both reasoning AND code generation? Explain your reasoning.""",
        "expected_tokens": 200
    },
    {
        "name": "Code Generation",
        "prompt": """Write a Python function that takes a list of task objects (with 'agent', 'status', 'priority' fields) and returns a prioritized execution plan. The plan should group tasks by agent and sort by priority (high > medium > low). Include docstring and type hints.""",
        "expected_tokens": 400
    },
    {
        "name": "Instruction Following",
        "prompt": """Create a task execution plan following these rules EXACTLY:
1. Output ONLY a JSON object
2. Include exactly 3 steps
3. Each step must have: step_id (number), action (string), depends_on (array)
4. Step 1's action must be "initialize"
5. Step 3 must depend on step 2
6. No markdown, no explanation, just JSON

Do NOT add any text before or after the JSON.""",
        "expected_tokens": 150
    },
    {
        "name": "Tool Selection Logic",
        "prompt": """You are a router agent. Available tools:
- web_search: for finding current information
- code_execute: for running Python code
- file_read: for reading local files
- image_generate: for creating images

User request: "Create a visualization of Bitcoin price over the last week"

Which tool(s) should you call and in what order? Provide step-by-step reasoning.""",
        "expected_tokens": 200
    },
    {
        "name": "Multi-step Reasoning",
        "prompt": """You need to coordinate 3 agents to solve: "Research the latest version of React, then create a code example, then review it for best practices"

Break this into subtasks showing:
1. Which agent handles each subtask
2. Dependencies between subtasks (what must finish before what starts)
3. Expected output format from each agent
4. How to combine outputs at the end""",
        "expected_tokens": 350
    }
]

def run_test(test):
    print(f"\n{'='*60}")
    print(f"TEST: {test['name']}")
    print(f"{'='*60}")
    
    start_time = time.time()
    
    # Build the curl command
    data = {
        "model": MODEL,
        "stream": False,
        "options": {
            "num_ctx": 4096,
            "temperature": 0.7,
            "num_predict": test['expected_tokens']
        },
        "messages": [
            {"role": "user", "content": test['prompt']}
        ]
    }
    
    cmd = [
        "curl", "-s", "http://localhost:11434/api/chat",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(data)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    elapsed = time.time() - start_time
    
    try:
        response = json.loads(result.stdout)
        content = response.get('message', {}).get('content', 'ERROR: No content')
        tokens_eval = response.get('eval_count', 0)
        tokens_prompt = response.get('prompt_eval_count', 0)
    except:
        content = f"ERROR parsing response: {result.stdout[:500]}"
        tokens_eval = 0
        tokens_prompt = 0
    
    print(f"\n⏱️  Time: {elapsed:.2f}s")
    print(f"📝 Tokens prompt: {tokens_prompt}")
    print(f"📝 Tokens generated: {tokens_eval}")
    print(f"⚡ Speed: {tokens_eval/elapsed:.1f} tok/s" if elapsed > 0 else "⚡ Speed: N/A")
    print(f"\n📤 Response (first 500 chars):\n{content[:500]}...")
    
    return {
        "name": test['name'],
        "time": elapsed,
        "tokens_prompt": tokens_prompt,
        "tokens_generated": tokens_eval,
        "speed": tokens_eval/elapsed if elapsed > 0 else 0,
        "response_preview": content[:300]
    }

def main():
    print(f"🧪 Benchmarking {MODEL} for Multi-Agent Use")
    print(f"⏰ Started at: {time.strftime('%H:%M:%S')}")
    
    results = []
    for test in TESTS:
        try:
            result = run_test(test)
            results.append(result)
        except Exception as e:
            print(f"❌ ERROR in {test['name']}: {e}")
            results.append({
                "name": test['name'],
                "error": str(e)
            })
    
    # Summary
    print(f"\n\n{'='*60}")
    print("📊 SUMMARY")
    print(f"{'='*60}")
    
    total_time = sum(r.get('time', 0) for r in results if 'time' in r)
    total_tokens = sum(r.get('tokens_generated', 0) for r in results if 'tokens_generated' in r)
    
    print(f"\nTotal tests: {len(results)}")
    print(f"Total time: {total_time:.1f}s")
    print(f"Total tokens generated: {total_tokens}")
    print(f"Overall speed: {total_tokens/total_time:.1f} tok/s" if total_time > 0 else "N/A")
    
    print(f"\n{'Test':<25} {'Time':>8} {'Speed':>10} {'Rating'}")
    print("-" * 60)
    for r in results:
        if 'time' in r:
            rating = "⭐" if r['speed'] > 10 else "🟡" if r['speed'] > 5 else "🐢"
            print(f"{r['name']:<25} {r['time']:>7.1f}s {r['speed']:>8.1f} tok/s {rating}")
        else:
            print(f"{r['name']:<25} {'ERROR':>20}")
    
    # Save results
    with open("/home/lumen/.openclaw/workspace/qwen32b_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n💾 Full results saved to: qwen32b_results.json")

if __name__ == "__main__":
    main()
