with open('frontend/src/app/page.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

target = '''            ) : planData ? (
              <div style={{ maxWidth: "860px", margin: "0 auto", width: "100%", display: "flex", flexDirection: "column" }}>
                <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 4px", marginBottom: "16px" }}>
                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab("viewer")}
                      style={{
                        padding: "7px 16px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer",
                        border: "none",
                        backgroundColor: activeViewTab === "viewer" ? "#4f46e5" : "#e2e8f0",
                        color: activeViewTab === "viewer" ? "#ffffff" : "#334155",
                      }}
                    >
                      📄 Table Viewer
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab("editor")}
                      style={{
                        padding: "7px 16px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer",
                        border: "none",
                        backgroundColor: activeViewTab === "editor" ? "#4f46e5" : "#e2e8f0",
                        color: activeViewTab === "editor" ? "#ffffff" : "#334155",
                      }}
                    >
                      ✏️ Structural Editor
                    </button>
                  </div>
                  <span style={{ fontSize: "11px", color: "#64748b", fontWeight: "600" }}>
                    LEARN Practice Teaching Layout
                  </span>
                </div>

                {activeViewTab === "viewer" && (
                  <>
                    {multiPeriodPlans && multiPeriodPlans.length > 1 ? (
                      <MultiPeriodPlanViewer
                        plans={multiPeriodPlans}
                        onNewPlan={() => {
                          setPlanData(null);
                          setMultiPeriodPlans([]);
                        }}
                        onEditPlan={(chosenPlan) => {
                          setPlanData((prev) =>
                            prev ? { ...prev, lesson_plan: chosenPlan as any } : null
                          );
                          setActiveViewTab("editor");
                        }}
                      />
                    ) : (
                      <LessonPlanViewer
                        plan={planData.lesson_plan}
                        factCheck={planData.fact_check_report}
                        alignment={planData.alignment_report}
                        filename={currentPlanFilename || undefined}
                        onEditInGenerator={() => setActiveViewTab("editor")}
                        onDeletePlan={currentPlanFilename ? () => setIsDeleteModalOpen(true) : undefined}
                      />
                    )}

                    <DeleteConfirmModal
                      isOpen={isDeleteModalOpen}
                      filename={currentPlanFilename || ""}
                      planTitle={planData?.lesson_plan?.lesson || planData?.lesson_plan?.competence || ""}
                      grade={planData?.lesson_plan?.grade}
                      subject={planData?.lesson_plan?.subject}
                      competenceLevel={planData?.lesson_plan?.competence_level}
                      timeAllocation={planData?.lesson_plan?.time_allocation}
                      isDeleting={isDeleting}
                      onConfirm={handleDeleteCurrentPlan}
                      onCancel={() => setIsDeleteModalOpen(false)}
                    />
                  </>
                )}

                {activeViewTab === "editor" && (
                  <StructuralEditor
                    initialPlan={planData.lesson_plan as any}
                    filename={currentPlanFilename || undefined}
                    onSave={(updated) => {
                      setPlanData((prev) => (prev ? { ...prev, lesson_plan: updated as any } : null));
                      setNotificationMessage("Updated lesson plan saved successfully!");
                      setTimeout(() => setNotificationMessage(null), 3000);
                    }}
                  />
                )}
              </div>'''

replacement = '''            ) : planData ? (
              <div
                style={{
                  backgroundColor: "#ffffff",
                  padding: "24px",
                  borderRadius: "16px",
                  border: "1px solid #e2e8f0",
                  boxShadow: "0 4px 6px -1px rgba(0, 0, 0, 0.05)",
                  display: "flex",
                  flexDirection: "column",
                  gap: "18px",
                  maxWidth: "860px",
                  margin: "0 auto",
                  width: "100%",
                  boxSizing: "border-box",
                }}
              >
                {/* Panel Header matching LessonPlanForm */}
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "space-between",
                    borderBottom: "1px solid #f1f5f9",
                    paddingBottom: "12px",
                    flexWrap: "wrap",
                    gap: "12px",
                  }}
                >
                  <div>
                    <h3
                      style={{
                        fontSize: "16px",
                        fontWeight: "800",
                        color: "#0f172a",
                        display: "flex",
                        alignItems: "center",
                        gap: "8px",
                        margin: 0,
                      }}
                    >
                      <span>📄</span>
                      <span>Generated Lesson Plan</span>
                    </h3>
                    <p style={{ fontSize: "12px", color: "#64748b", margin: "2px 0 0 0" }}>
                      LEARN Practice Teaching Layout • Table Viewer and Structural Editor
                    </p>
                  </div>

                  <div style={{ display: "flex", gap: "8px" }}>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab("viewer")}
                      style={{
                        padding: "7px 16px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer",
                        border: "none",
                        backgroundColor: activeViewTab === "viewer" ? "#4f46e5" : "#e2e8f0",
                        color: activeViewTab === "viewer" ? "#ffffff" : "#334155",
                        boxShadow: activeViewTab === "viewer" ? "0 2px 4px rgba(79, 70, 229, 0.25)" : "none",
                        transition: "all 0.15s ease",
                      }}
                    >
                      📄 Table Viewer
                    </button>
                    <button
                      type="button"
                      onClick={() => setActiveViewTab("editor")}
                      style={{
                        padding: "7px 16px",
                        borderRadius: "10px",
                        fontSize: "12px",
                        fontWeight: "700",
                        cursor: "pointer",
                        border: "none",
                        backgroundColor: activeViewTab === "editor" ? "#4f46e5" : "#e2e8f0",
                        color: activeViewTab === "editor" ? "#ffffff" : "#334155",
                        boxShadow: activeViewTab === "editor" ? "0 2px 4px rgba(79, 70, 229, 0.25)" : "none",
                        transition: "all 0.15s ease",
                      }}
                    >
                      ✏️ Structural Editor
                    </button>
                  </div>
                </div>

                {activeViewTab === "viewer" && (
                  <>
                    {multiPeriodPlans && multiPeriodPlans.length > 1 ? (
                      <MultiPeriodPlanViewer
                        plans={multiPeriodPlans}
                        onNewPlan={() => {
                          setPlanData(null);
                          setMultiPeriodPlans([]);
                        }}
                        onEditPlan={(chosenPlan) => {
                          setPlanData((prev) =>
                            prev ? { ...prev, lesson_plan: chosenPlan as any } : null
                          );
                          setActiveViewTab("editor");
                        }}
                      />
                    ) : (
                      <LessonPlanViewer
                        plan={planData.lesson_plan}
                        factCheck={planData.fact_check_report}
                        alignment={planData.alignment_report}
                        filename={currentPlanFilename || undefined}
                        onEditInGenerator={() => setActiveViewTab("editor")}
                        onDeletePlan={currentPlanFilename ? () => setIsDeleteModalOpen(true) : undefined}
                        embedded={true}
                      />
                    )}

                    <DeleteConfirmModal
                      isOpen={isDeleteModalOpen}
                      filename={currentPlanFilename || ""}
                      planTitle={planData?.lesson_plan?.lesson || planData?.lesson_plan?.competence || ""}
                      grade={planData?.lesson_plan?.grade}
                      subject={planData?.lesson_plan?.subject}
                      competenceLevel={planData?.lesson_plan?.competence_level}
                      timeAllocation={planData?.lesson_plan?.time_allocation}
                      isDeleting={isDeleting}
                      onConfirm={handleDeleteCurrentPlan}
                      onCancel={() => setIsDeleteModalOpen(false)}
                    />
                  </>
                )}

                {activeViewTab === "editor" && (
                  <StructuralEditor
                    initialPlan={planData.lesson_plan as any}
                    filename={currentPlanFilename || undefined}
                    embedded={true}
                    onSave={(updated) => {
                      setPlanData((prev) => (prev ? { ...prev, lesson_plan: updated as any } : null));
                      setNotificationMessage("Updated lesson plan saved successfully!");
                      setTimeout(() => setNotificationMessage(null), 3000);
                    }}
                  />
                )}
              </div>'''

# Normalize newlines
def norm(s):
    return s.replace('\r\n', '\n')

content_norm = norm(content)
target_norm = norm(target)

assert target_norm in content_norm, 'target_norm not found in content'

new_content = content_norm.replace(target_norm, norm(replacement), 1)

# Preserve original line endings if CRLF
if '\r\n' in content:
    new_content = new_content.replace('\n', '\r\n')

with open('frontend/src/app/page.tsx', 'w', encoding='utf-8') as f:
    f.write(new_content)

print('frontend/src/app/page.tsx updated successfully!')

