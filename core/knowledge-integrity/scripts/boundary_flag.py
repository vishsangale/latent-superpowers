#!/usr/bin/env python3
"""Tool to enforce boundary tagging on agent outputs."""

import argparse

def main():
    parser = argparse.ArgumentParser(description="Boundary Tag Enforcer")
    parser.add_argument("--source", choices=["training", "retrieval", "inference"], required=True)
    args = parser.parse_args()

    if args.source == "training":
        print("TAG TO USE: [Source: Training Prior]")
        print("Warning: This relies on internal pre-training knowledge which may be outdated or hallucinated.")
    elif args.source == "retrieval":
        print("TAG TO USE: [Source: Retrieved Evidence]")
        print("Required: You must provide the URL/Reference for the retrieved document.")
    elif args.source == "inference":
        print("TAG TO USE: [Source: Logical Inference]")
        print("Warning: This is a reasoned deduction, NOT empirical fact. State this clearly.")
        
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
