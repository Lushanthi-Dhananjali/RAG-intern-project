with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Add selectedClassicPeriodIndex state
old_state = '''  const [multiPeriodPlans, setMultiPeriodPlans] = useState<LessonPlanSchemaDto[]>([]);'''

new_state = '''  const [multiPeriodPlans, setMultiPeriodPlans] = useState<LessonPlanSchemaDto[]>([]);
  const [selectedClassicPeriodIndex, setSelectedClassicPeriodIndex] = useState<number>(0);'''

assert old_state in content, 'old_state not found'
content = content.replace(old_state, new_state, 1)

# 2. Reset selectedClassicPeriodIndex in handleStandardGenerate
old_handle_std = '''      const plans =
        Array.isArray(result.lesson_plans) && result.lesson_plans.length > 0
          ? result.lesson_plans
          : [result.lesson_plan as any];
      setMultiPeriodPlans(plans as any);
      setCurrentPlanFilename(null);
      setActiveViewTab("viewer");'''

new_handle_std = '''      const plans =
        Array.isArray(result.lesson_plans) && result.lesson_plans.length > 0
          ? result.lesson_plans
          : [result.lesson_plan as any];
      setMultiPeriodPlans(plans as any);
      setSelectedClassicPeriodIndex(0);
      setCurrentPlanFilename(null);
      setActiveViewTab("viewer");'''

assert old_handle_std in content, 'old_handle_std not found'
content = content.replace(old_handle_std, new_handle_std, 1)

# 3. Reset selectedClassicPeriodIndex in handleLoadPlanToViewer
old_handle_load = '''    setMultiPeriodPlans([savedPlan as any]);
    setGenerationMode("standard");
    setActiveViewTab("viewer");'''

new_handle_load = '''    setMultiPeriodPlans([savedPlan as any]);
    setSelectedClassicPeriodIndex(0);
    setGenerationMode("standard");
    setActiveViewTab("viewer");'''

assert old_handle_load in content, 'old_handle_load not found'
content = content.replace(old_handle_load, new_handle_load, 1)

# 4. Define activePlanToView before JSX
old_jsx_start = '''  if (authStatus !== "authenticated") {'''

new_jsx_start = '''  const activePlanToView =
    multiPeriodPlans && multiPeriodPlans.length > selectedClassicPeriodIndex
      ? multiPeriodPlans[selectedClassicPeriodIndex]
      : planData?.lesson_plan;

  if (authStatus !== "authenticated") {'''

assert old_jsx_start in content, 'old_jsx_start not found'
content = content.replace(old_jsx_start, new_jsx_start, 1)

# 5. Replace Classic Generator planData rendering
# Find from ) : planData ? ( to ) : (
target_plan_data_start = '            ) : planData ? ('
target_plan_data_end = '            ) : (\n              <div\n                style={{\n                  backgroundColor: "#ffffff",\n                  padding: "36px 24px",'

# Let's inspect where this is
idx_start = content.find(target_plan_data_start)
assert idx_start != -1, 'target_plan_data_start not found'
idx_end = content.find('            ) : (\n              <div', idx_start)
if idx_end == -1:
    idx_end = content.find('            ) : (\r\n              <div', idx_start)
assert idx_end != -1, 'target_plan_data_end not found'

old_plan_data_section = content[idx_start:idx_end]

new_plan_data_section = '''            ) : planData ? (
              <div style={{ maxWidth: "860px", margin: "0 auto", width: "100%" }}>
                {activeViewTab === "viewer" ? (
                  <>
                    <LessonPlanViewer
                      plan={activePlanToView}
                      factCheck={planData.fact_check_report}
                      alignment={planData.alignment_report}
                      filename={currentPlanFilename || undefined}
                      allPlans={multiPeriodPlans && multiPeriodPlans.length > 1 ? multiPeriodPlans : undefined}
                      activePeriodIndex={selectedClassicPeriodIndex}
                      onPeriodChange={(newIdx) => setSelectedClassicPeriodIndex(newIdx)}
                      activeViewTab={activeViewTab}
                      onViewTabChange={setActiveViewTab}
                      onDeletePlan={currentPlanFilename ? () => setIsDeleteModalOpen(true) : undefined}
                    />

                    <DeleteConfirmModal
                      isOpen={isDeleteModalOpen}
                      filename={currentPlanFilename || ""}
                      planTitle={activePlanToView?.lesson || activePlanToView?.competence || ""}
                      grade={activePlanToView?.grade}
                      subject={activePlanToView?.subject}
                      competenceLevel={activePlanToView?.competence_level}
                      timeAllocation={activePlanToView?.time_allocation}
                      isDeleting={isDeleting}
                      onConfirm={handleDeleteCurrentPlan}
                      onCancel={() => setIsDeleteModalOpen(false)}
                    />
                  </>
                ) : (
                  <StructuralEditor
                    initialPlan={activePlanToView as any}
                    filename={currentPlanFilename || undefined}
                    activeViewTab={activeViewTab}
                    onViewTabChange={setActiveViewTab}
                    onSave={(updated) => {
                      setPlanData((prev) => (prev ? { ...prev, lesson_plan: updated as any } : null));
                      if (multiPeriodPlans && multiPeriodPlans.length > 0) {
                        const updatedList = [...multiPeriodPlans];
                        updatedList[selectedClassicPeriodIndex] = updated as any;
                        setMultiPeriodPlans(updatedList);
                      }
                      setNotificationMessage("Updated lesson plan saved successfully!");
                      setTimeout(() => setNotificationMessage(null), 3000);
                    }}
                  />
                )}
              </div>
'''

content = content[:idx_start] + new_plan_data_section + content[idx_end:]

with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('frontend/src/app/page.tsx successfully updated!')

