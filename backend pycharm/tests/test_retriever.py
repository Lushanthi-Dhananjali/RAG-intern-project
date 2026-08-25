from multi_grade_retriever import MultiGradeBoundaryRetriever

retriever = MultiGradeBoundaryRetriever()

query_topic = "Protecting the environment: waste segregation, tree planting, and water preservation"
results = retriever.retrieve_3tier_boundaries(
    query=query_topic,
    target_grade="Grade 8",
    subject="Civic Education"
)

print("\n" + "=" * 80)
print(f"🔍 3-TIER RETRIEVAL TEST FOR: {results['query']}")
print("=" * 80)

# TIER 1
print(f"\n🎯 [TIER 1 - Target Content (Grade 8)]: {len(results['tier_1_target_content'])} distinct chunks found")
for idx, item in enumerate(results["tier_1_target_content"], 1):
    preview = item['content'][:120].replace('\n', ' ')
    print(f"  [{idx}] ID: {item['id']}")
    print(f"      Source: {item['source']} | Type: {item['doc_type']} | Comp: {item['competency']}")
    print(f"      Text: \"{preview}...\"\n")

# TIER 2
print(f"🧱 [TIER 2 - Prerequisite Baseline (Grade 7)]: {len(results['tier_2_prerequisites'])} distinct chunks found")
for idx, item in enumerate(results["tier_2_prerequisites"], 1):
    preview = item['content'][:120].replace('\n', ' ')
    print(f"  [{idx}] ID: {item['id']}")
    print(f"      Source: {item['source']} | Comp: {item['competency']}")
    print(f"      Text: \"{preview}...\"\n")

# TIER 3
print(f"🚫 [TIER 3 - Upper Boundary Limits (Grade 9)]: {len(results['tier_3_upper_boundaries'])} distinct chunks found")
for idx, item in enumerate(results["tier_3_upper_boundaries"], 1):
    preview = item['content'][:120].replace('\n', ' ')
    print(f"  [{idx}] ID: {item['id']}")
    print(f"      Source: {item['source']} | Comp: {item['competency']}")
    print(f"      Text: \"{preview}...\"\n")

# EXEMPLARS
print(f"🌱 [EXEMPLARS - Practical Activities]: {len(results['practical_exemplars'])} chunks found")
for idx, item in enumerate(results["practical_exemplars"], 1):
    preview = item['content'][:120].replace('\n', ' ')
    print(f"  [{idx}] ID: {item['id']}")
    print(f"      Source: {item['source']} | Type: {item['doc_type']}")
    print(f"      Text: \"{preview}...\"\n")