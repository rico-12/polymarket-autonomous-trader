#!/usr/bin/env python3
"""
3-Day Evaluation & Learning System
Evaluates trading performance and provides improvements
"""

import os
import sys
import json
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))
from signal_logger import (
    load_log, save_log, evaluate_performance, 
    get_signals, get_positions, generate_signal_reasoning
)

EVAL_LOG = Path(__file__).parent / "evaluations.json"

def load_eval_log():
    if EVAL_LOG.exists():
        with open(EVAL_LOG, 'r') as f:
            return json.load(f)
    return {"evaluations": [], "improvements": [], "last_run": None}

def save_eval_log(data):
    with open(EVAL_LOG, 'w') as f:
        json.dump(data, f, indent=2)

def run_evaluation():
    """Run full evaluation"""
    print("=" * 60)
    print("📊 3-DAY TRADING EVALUATION")
    print("=" * 60)
    
    # Get performance data
    perf = evaluate_performance()
    
    # Print summary
    print(f"\n📈 SUMMARY (Last 30 days)")
    print("-" * 40)
    print(f"  Total Positions: {perf['total_positions']}")
    print(f"  Closed: {perf['closed_positions']}")
    print(f"  Open: {perf['open_positions']}")
    print(f"  Wins: {perf['wins']}")
    print(f"  Losses: {perf['losses']}")
    print(f"  Win Rate: {perf['win_rate']}%")
    
    print(f"\n🎯 RECOMMENDATIONS")
    print("-" * 40)
    for rec in perf.get('recommendations', []):
        print(f"  {rec}")
    
    # Save evaluation
    eval_data = load_eval_log()
    
    eval_entry = {
        "timestamp": datetime.now().isoformat(),
        "performance": perf,
        "signals_analyzed": len(perf.get('recent_signals', []))
    }
    
    eval_data["evaluations"].append(eval_entry)
    eval_data["last_run"] = datetime.now().isoformat()
    save_eval_log(eval_data)
    
    # Check if improvement is needed
    if perf['win_rate'] < 40:
        print("\n⚠️ WARNING: Win rate below 40%")
        suggest_threshold_increase(perf)
    
    print("\n" + "=" * 60)
    print("✅ Evaluation complete!")
    print("=" * 60)
    
    return perf

def suggest_threshold_increase(perf):
    """Suggest increasing score threshold based on data"""
    signals = perf.get('recent_signals', [])
    
    if not signals:
        return
    
    # Analyze winning signals
    winning_scores = []
    losing_scores = []
    
    # This would need actual position results - placeholder
    avg_score = sum(s.get('score', 50) for s in signals) / len(signals)
    
    print(f"\n📊 Average signal score: {avg_score:.1f}")
    
    if avg_score < 55:
        print("   💡 Consider increasing threshold to 55+")
    elif avg_score < 60:
        print("   💡 Consider increasing threshold to 60+")

def check_and_learn():
    """Main learning function - call this regularly"""
    eval_data = load_eval_log()
    
    last_run = eval_data.get("last_run")
    if last_run:
        last_date = datetime.fromisoformat(last_run)
        days_since = (datetime.now() - last_date).days
        
        if days_since < 3:
            print(f"⏳ Next evaluation in {3 - days_since} days")
            return
    
    # Run evaluation
    run_evaluation()

def generate_improvement_report():
    """Generate comprehensive improvement report"""
    eval_data = load_eval_log()
    perf = evaluate_performance()
    
    report = {
        "generated_at": datetime.now().isoformat(),
        "win_rate": perf['win_rate'],
        "total_trades": perf['total_positions'],
        "improvements_made": [],
        "learnings": []
    }
    
    # Analyze patterns
    if perf.get('indicator_performance'):
        for ind, stats in perf['indicator_performance'].items():
            if stats['total'] >= 3:
                win_rate_ind = stats['wins'] / stats['total'] * 100
                
                if win_rate_ind > 70:
                    report['learnings'].append({
                        "indicator": ind[:50],
                        "win_rate": win_rate_ind,
                        "recommendation": "PRIORITIZE - high success rate"
                    })
                elif win_rate_ind < 30:
                    report['learnings'].append({
                        "indicator": ind[:50],
                        "win_rate": win_rate_ind,
                        "recommendation": "AVOID - low success rate"
                    })
    
    # Add improvements
    eval_data["improvements"].append(report)
    save_eval_log(eval_data)
    
    return report

if __name__ == "__main__":
    check_and_learn()