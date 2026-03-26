"""
Main Pipeline Entry Point
Runs the full stock analysis and saves results.
"""
import sys
import argparse
from datetime import datetime

from recommendation_engine import run_full_analysis, save_results
from alerts import send_alerts


def main():
    parser = argparse.ArgumentParser(description="🤖 Automated Stock Recommendation System")
    parser.add_argument("--timeframe", "-t", choices=["intraday", "short_term", "long_term", "all"],
                        default="all", help="Which timeframe to analyze (default: all)")
    parser.add_argument("--no-alerts", action="store_true", help="Skip sending alerts")
    parser.add_argument("--top", type=int, default=5, help="Number of top stocks in alerts")
    args = parser.parse_args()

    print("=" * 60)
    print("  🤖 Automated ML Stock Recommendation System")
    print(f"  📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    if args.timeframe == "all":
        results = run_full_analysis()
    else:
        from recommendation_engine import generate_recommendations
        results = {args.timeframe: generate_recommendations(args.timeframe)}

    # Save results
    output_file = save_results(results)

    # Print summary
    for tf, df in results.items():
        if not df.empty:
            print(f"\n{'─'*50}")
            print(f"  🏆 TOP 5 — {tf.replace('_',' ').upper()}")
            print(f"{'─'*50}")
            top5 = df.head(5)
            for _, row in top5.iterrows():
                print(f"  {row['Signal']}  {row['Symbol']:>12}  "
                      f"₹{row['Close']:>8}  Score: {row['Composite_Score']}")

    if not args.no_alerts:
        send_alerts(results, top_n=args.top)
        
    try:
        import os, json
        with open(os.path.join(os.path.dirname(__file__), "progress.json"), "w") as f:
            json.dump({"status": "idle"}, f)
    except Exception:
        pass

    print(f"\n✅ Analysis complete! Results saved to: {output_file}")
    return results


if __name__ == "__main__":
    main()
