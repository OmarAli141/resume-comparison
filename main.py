import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent_feature.graph import app as agent_app
from agent_feature.nodes import handle_clarification_response
from llm_comparison.llm_client import llm_comparative_analysis
from llm_comparison.scoring import score_candidates
from shared.candidate_search import (
    build_search_query,
    search_candidates,
    filter_by_job_title,
    apply_requirements_filter,
    clean_job_title_for_display,
)
from shared.contact_actions import contact_followup_flow
from design.display import (
    print_profile_table,
    print_similarity_table,
    print_llm_results,
    select_llm_backend,
)
from design.export import export_results_to_json


def main():
    print("Local AI Recruiter")
    print("═" * 50)

    while True:
        query = input("\nEnter your job query:\n→ ").strip()
        if query.lower() in {"quit", "exit", "q", "e"}:
            print("\nThank you! Your ATS is world-class.")
            break
        if not query:
            print("Please enter a valid job query.")
            continue

        try:
            # === Run LangGraph agent for clarification loop ===
            agent_state = {
                "user_query": query,
                "structured_query": {},
                "missing_fields": [],
                "query_complete": False,
                "final_response": "",
            }

            # Use LangGraph app for the clarification loop
            # The graph runs: understand -> (clarify or search)
            # When clarify ends, we pause for user input, then manually call handle_response
            config = {"recursion_limit": 50}
            
            # Keep running until query is complete
            while not agent_state.get("query_complete", False):
                # Run the graph - it will go: understand -> clarify -> handle_response -> understand
                # We pause between clarify and handle_response for user input
                for event in agent_app.stream(agent_state, config=config):
                    for node_name, node_output in event.items():
                        # Update state from node output
                        if isinstance(node_output, dict):
                            agent_state.update(node_output)
                        
                        # When we hit "clarify", pause for user input
                        if node_name == "clarify":
                            question = agent_state.get("final_response", "")
                            if question:
                                print(f"\n{question}")
                                answer = input("→ ").strip()
                                
                                # Add user answer to messages
                                if "messages" not in agent_state:
                                    agent_state["messages"] = []
                                agent_state["messages"].append({"role": "user", "content": answer})
                                
                                # Manually call handle_response since we broke the stream
                                response_update = handle_clarification_response(agent_state)
                                agent_state.update(response_update)
                                
                                # Break to restart the loop - graph will go to understand again
                                break
                        
                        # If query is complete, exit
                        if agent_state.get("query_complete", False):
                            break
                    
                    # Break if we processed clarify (got user input) or if query complete
                    if node_name == "clarify" or agent_state.get("query_complete", False):
                        break
                
                # Exit if query is complete
                if agent_state.get("query_complete", False):
                    break

            structured = agent_state.get("structured_query", {})
            
            # Build search query and search for candidates
            search_query = build_search_query(structured, query)
            candidates = search_candidates(search_query, top_k=20)
            
            # Filter by job title if specified
            job_title = structured.get("job_title")
            candidates, job_title_for_display = filter_by_job_title(candidates, job_title)
            
            # Apply requirements filtering
            candidates, filters = apply_requirements_filter(candidates, structured, search_query)
            
            # Display filters
            if filters:
                title_filters = []
                clean_title = clean_job_title_for_display(job_title_for_display)
                if clean_title:
                    title_filters.append(f"Job Title: {clean_title}")
                all_filters = title_filters + filters
                if all_filters:
                    print(f"\nApplied filters → {' | '.join(all_filters)}")

            candidates.sort(key=lambda x: x["similarity"], reverse=True)
            scored_candidates = score_candidates(candidates[:10], search_query)

            if not scored_candidates:
                print("No candidates matched your criteria.")
                continue

            similarity_ranked = sorted(scored_candidates, key=lambda x: x.get("similarity", 0), reverse=True)

            print_profile_table(similarity_ranked)
            print_similarity_table(similarity_ranked)

            select_llm_backend()

            top3 = similarity_ranked[:3]
            print(f"\nSending top 3 to AI recruiter...", flush=True)
            analysis = llm_comparative_analysis(top3, search_query, show_progress=True)
            print_llm_results(analysis)

            # === New post-analysis contact / LinkedIn flow ===
            contact_followup_flow(similarity_ranked)

            # === YOUR EXACT MENU ===
            while True:
                print("\n1. Download results as JSON file")
                print("2. Enter a new query")
                print("3. Exit")
                choice = input("Select an option (1-3): ").strip()

                if choice == "1":
                    try:
                        filepath = export_results_to_json(similarity_ranked, search_query, analysis)
                        print(f"\nResults exported successfully!")
                        print(f"   File: {filepath}")
                    except Exception as e:
                        print(f"\nError exporting results: {e}")

                elif choice == "2":
                    print()
                    break

                elif choice == "3":
                    print("\nThank you! Your ATS is world-class.")
                    sys.exit(0)

                else:
                    print("\nInvalid option. Please enter 1, 2, or 3.")

        except Exception as e:
            print(f"\nError: {e}")
            continue


if __name__ == "__main__":
    main()
