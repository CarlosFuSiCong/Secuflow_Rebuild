"use client";

import { useState, useEffect, useRef } from "react";
import Card from "@/components/horizon/Card";
import { ProjectCharts } from "./ProjectCharts";
import { DASHBOARD_TEXT } from "@/app/dashboard/constants";
import type { ProjectDetailsProps } from "@/lib/types";
import { useProjects } from "@/lib/hooks/useProjects";
import { getProject, getProjectBranches, switchBranch } from "@/lib/api/projects";
import { triggerSTCAnalysis, triggerMCSTCAnalysis } from "@/lib/api/stc";
import type { Project } from "@/lib/types/project";
import type { Branch } from "@/lib/types/project";
import {
  ProjectHeader,
  EmptyState,
  LoadingState,
  ErrorState
} from "./project-details";
import { STCMatrix } from "./project-details/STCMatrix";
import { AnalyticsHistory } from "./project-details/AnalyticsHistory";
import { CoordinationPairsModal } from "./project-details/CoordinationPairsModal";
import { ContributorRoleManagement } from "./ContributorRoleManagement";
import type { ProjectMember } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { PlayCircle, Loader2, GitBranch, Users, BarChart3, CheckCircle2, AlertCircle } from "lucide-react";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";

type AnalysisStep = "tnm" | "stc" | "classification" | "mcstc" | "complete";

/**
 * Convert repository_path to TNM output directory path
 * repository_path: /app/tnm_repositories/project_123
 * tnm_output_dir: /app/tnm_output/project_123
 */
function getTnmOutputDir(repositoryPath: string | undefined): string | null {
  if (!repositoryPath) return null;
  
  // Extract project_id from repository path
  const match = repositoryPath.match(/project_(\d+)/);
  if (!match) return null;
  
  const projectId = match[1];
  // Construct TNM output directory path
  return `/app/tnm_output/project_${projectId}`;
}

export function ProjectDetails({ projectId }: ProjectDetailsProps) {
  // State management
  const [selectedBranch, setSelectedBranch] = useState("main");
  const [activeTab, setActiveTab] = useState("workflow");
  const [project, setProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [branches, setBranches] = useState<Branch[]>([]);
  const [branchesLoading, setBranchesLoading] = useState(false);
  const [runningTNMAnalysis, setRunningTNMAnalysis] = useState(false);
  const [runningSTCAnalysis, setRunningSTCAnalysis] = useState(false);
  const [runningMCSTCAnalysis, setRunningMCSTCAnalysis] = useState(false);
  const [analysisMessage, setAnalysisMessage] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState<AnalysisStep>("tnm");
  const [selectedSTCId, setSelectedSTCId] = useState<string | undefined>(undefined);
  
  // Use ref for pollInterval to persist across renders and avoid closure issues
  const pollIntervalRef = useRef<NodeJS.Timeout | null>(null);
  const [selectedMCSTCId, setSelectedMCSTCId] = useState<string | undefined>(undefined);
  const [detailsBranch, setDetailsBranch] = useState<string>("main");
  const [showDetailsModal, setShowDetailsModal] = useState(false);
  const [isSwitchingBranch, setIsSwitchingBranch] = useState(false);

  const { allProjects } = useProjects();

  // Fetch project details
  useEffect(() => {
    if (!projectId) {
      setProject(null);
      setBranches([]);
      return;
    }

    const fetchProjectDetails = async () => {
      setLoading(true);
      setError(null);

      try {
        const projectData = await getProject(projectId);
        setProject(projectData);
        
        // Determine current step based on project data
        if (!projectData.repository_path) {
          setCurrentStep("tnm");
        } else if (!projectData.last_risk_check_at) {
          setCurrentStep("stc");
        } else if (projectData.mcstc_risk_score !== null && projectData.mcstc_risk_score !== undefined) {
          setCurrentStep("complete");
        } else {
          setCurrentStep("classification");
        }
      } catch (err: any) {
        console.error("Failed to fetch project details:", err);
        setError(err?.response?.data?.message || "Failed to load project details");
      } finally {
        setLoading(false);
      }
    };

    fetchProjectDetails();

    // Poll for TNM completion if needed
    const startPolling = async () => {
      try {
        const projectData = await getProject(projectId);
        const tnmComplete = !!projectData.repository_path;
        
        if (!tnmComplete) {
          pollIntervalRef.current = setInterval(async () => {
            try {
              const updatedProject = await getProject(projectId);
              setProject(updatedProject);
              
              if (updatedProject.repository_path && pollIntervalRef.current) {
                clearInterval(pollIntervalRef.current);
                pollIntervalRef.current = null;
              }
            } catch (err) {
              console.error("Error polling project status:", err);
            }
          }, 10000);
        }
      } catch (err) {
        console.error("Error checking if polling needed:", err);
      }
    };

    startPolling();

    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
        pollIntervalRef.current = null;
      }
    };
  }, [projectId]);

  // Fetch branches
  useEffect(() => {
    if (!projectId) {
      setBranches([]);
      return;
    }

    const fetchBranches = async () => {
      setBranchesLoading(true);
      try {
        const branchesData = await getProjectBranches(projectId);
        setBranches(branchesData.branches || []);
        // Set default branch from project or first branch
        if (project?.default_branch) {
          setSelectedBranch(project.default_branch);
        } else if (branchesData.branches && branchesData.branches.length > 0) {
          setSelectedBranch(branchesData.branches[0].name);
        }
      } catch (err) {
        console.error("Failed to fetch branches:", err);
        setBranches([]);
      } finally {
        setBranchesLoading(false);
      }
    };

    fetchBranches();
  }, [projectId, project?.default_branch]);

  // Handle TNM re-run
  const handleRunTNMAnalysis = async () => {
    setRunningTNMAnalysis(true);
    setAnalysisMessage(null);
    try {
      // Backend endpoint not yet implemented
      setAnalysisMessage("TNM re-run functionality is not yet available. Please contact support.");
    } catch (err: any) {
      console.error("Failed to trigger TNM analysis:", err);
      setAnalysisMessage(err?.response?.data?.message || "Failed to start TNM analysis");
    } finally {
      setRunningTNMAnalysis(false);
    }
  };

  // Handle branch switch confirmation
  const handleConfirmBranchSwitch = async (newBranch: string) => {
    setRunningTNMAnalysis(true);
    setIsSwitchingBranch(true);
    setAnalysisMessage(`Switching to branch ${newBranch}...`);
    setCurrentStep("tnm");
    
    try {
      // Find the branch data for the selected branch
      const targetBranch = branches.find(b => b.name === newBranch);
      if (!targetBranch) {
        throw new Error(`Branch ${newBranch} not found`);
      }

      // Check if branch_id exists
      if (!targetBranch.branch_id) {
        throw new Error(`Branch ${newBranch} does not have a branch_id. Please refresh the branches.`);
      }

      // Call backend API to switch branch
      const result = await switchBranch(projectId, targetBranch.branch_id);
      
      setAnalysisMessage(`Successfully switched to ${newBranch}. Repository will be re-analyzed.`);
      
      // Update project data - DON'T reset anything, let backend data flow naturally
      setProject(result.project);
      
      // Update current branch immediately for UI feedback
      setSelectedBranch(result.current_branch);
      
      // Refresh branches in background
      try {
        const branchesData = await getProjectBranches(projectId);
        setBranches(branchesData.branches);
        setSelectedBranch(branchesData.current_branch);
      } catch (branchError) {
        console.error("Failed to refresh branches:", branchError);
        // Continue even if branch refresh fails
      }
      
      // Note: TNM analysis will be triggered automatically by the backend after branch switch
      // Immediately poll once to get initial state
      try {
        const initialProject = await getProject(projectId);
        console.log('Initial project state after switch:', {
          repository_path: initialProject.repository_path,
          last_risk_check_at: initialProject.last_risk_check_at,
          members_count: initialProject.members_count
        });
        setProject(initialProject);
        
        // If TNM is already complete, don't start polling
        if (initialProject.repository_path) {
          setAnalysisMessage(`Branch switched and TNM analysis already completed for ${newBranch}!`);
          setCurrentStep("stc");
          setRunningTNMAnalysis(false);
          setIsSwitchingBranch(false);
          return; // Exit early
        }
      } catch (err) {
        console.error("Error getting initial project state:", err);
      }
      
      // Start polling for TNM completion
      let pollCount = 0;
      const maxPolls = 60; // 5 minutes max (60 * 5s)
      
      const pollInterval = setInterval(async () => {
        pollCount++;
        
        try {
          const updatedProject = await getProject(projectId);
          
          setProject(updatedProject);
          
          // If TNM is complete, stop polling
          if (updatedProject.repository_path) {
            clearInterval(pollInterval);
            setAnalysisMessage(`Branch switched and TNM analysis completed for ${newBranch}!`);
            setCurrentStep("stc");
            setRunningTNMAnalysis(false);
            setIsSwitchingBranch(false);
          } else if (pollCount >= maxPolls) {
            clearInterval(pollInterval);
            setAnalysisMessage('TNM analysis is taking longer than expected. Please refresh the page to check status.');
            setRunningTNMAnalysis(false);
            setIsSwitchingBranch(false);
          }
        } catch (err) {
          console.error("Error polling project status:", err);
          // On error, stop polling to prevent infinite failures
          clearInterval(pollInterval);
          setAnalysisMessage('Error checking analysis status. Please refresh the page.');
          setRunningTNMAnalysis(false);
          setIsSwitchingBranch(false);
        }
      }, 5000); // Poll every 5 seconds
      
    } catch (err: any) {
      console.error("Failed to switch branch:", err);
      const errorMessage = err?.response?.data?.errorMessage 
        || err?.response?.data?.message 
        || err.message 
        || "Failed to switch branch";
      setAnalysisMessage(errorMessage);
      setRunningTNMAnalysis(false);
      setIsSwitchingBranch(false);
    }
  };

  // Handle STC analysis
  const handleRunSTCAnalysis = async () => {
    const tnmOutputDir = getTnmOutputDir(project?.repository_path);
    
    if (!tnmOutputDir) {
      setAnalysisMessage("TNM output directory not available. Please complete TNM analysis first.");
      return;
    }
    
    setRunningSTCAnalysis(true);
    setAnalysisMessage(null);
    try {
      await triggerSTCAnalysis(projectId, selectedBranch, tnmOutputDir);
      setAnalysisMessage("STC analysis started successfully!");
      setTimeout(async () => {
        const updatedProject = await getProject(projectId);
        setProject(updatedProject);
        setCurrentStep("classification");
      }, 3000);
    } catch (err: any) {
      console.error("Failed to trigger STC analysis:", err);
      setAnalysisMessage(err?.response?.data?.message || "Failed to start STC analysis");
    } finally {
      setRunningSTCAnalysis(false);
    }
  };

  // Handle MC-STC analysis
  const handleRunMCSTCAnalysis = async () => {
    const tnmOutputDir = getTnmOutputDir(project?.repository_path);
    
    if (!tnmOutputDir) {
      setAnalysisMessage("TNM output directory not available. Please complete TNM analysis first.");
      return;
    }
    
    setRunningMCSTCAnalysis(true);
    setAnalysisMessage(null);
    try {
      await triggerMCSTCAnalysis(projectId, selectedBranch, tnmOutputDir);
      setAnalysisMessage("MC-STC analysis started successfully!");
      setTimeout(async () => {
        const updatedProject = await getProject(projectId);
        setProject(updatedProject);
        setCurrentStep("complete");
      }, 3000);
    } catch (err: any) {
      console.error("Failed to trigger MC-STC analysis:", err);
      setAnalysisMessage(err?.response?.data?.message || "Failed to start MC-STC analysis");
    } finally {
      setRunningMCSTCAnalysis(false);
    }
  };

  // Handle viewing details from history
  const handleViewDetails = (data: { stcId?: string; mcstcId?: string; branch: string }) => {
    setSelectedSTCId(data.stcId);
    setSelectedMCSTCId(data.mcstcId);
    setDetailsBranch(data.branch);
    setShowDetailsModal(true);
  };

  const handleCloseDetails = () => {
    setShowDetailsModal(false);
    setSelectedSTCId(undefined);
    setSelectedMCSTCId(undefined);
  };

  // Render step indicator
  const renderStepIndicator = (step: AnalysisStep, label: string, icon: React.ReactNode) => {
    // Analysis Pipeline should reflect workflow state (currentStep)
    // NOT historical project data (for branch switching scenarios)
    const isCurrent = currentStep === step;
    
    // A step is complete ONLY if it's before the current step in the workflow
    const stepOrder: AnalysisStep[] = ["tnm", "stc", "classification", "mcstc", "complete"];
    const currentStepIndex = stepOrder.indexOf(currentStep);
    const thisStepIndex = stepOrder.indexOf(step);
    
    // Only show as complete if this step comes before current step
    const isComplete = thisStepIndex < currentStepIndex;
    
    return (
      <div className={`flex items-center gap-3 p-4 rounded-lg border-2 transition-all ${
        isComplete ? "border-green-500 bg-green-50 dark:bg-green-950/20" :
        isCurrent ? "border-blue-500 bg-blue-50 dark:bg-blue-950/20" :
        "border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-900/20"
      }`}>
        <div className={`p-2 rounded-full ${
          isComplete ? "bg-green-500 text-white" :
          isCurrent ? "bg-blue-500 text-white" :
          "bg-gray-300 dark:bg-gray-700 text-gray-600 dark:text-gray-400"
        }`}>
          {isComplete ? <CheckCircle2 className="h-5 w-5" /> : icon}
        </div>
        <div className="flex-1">
          <div className="font-semibold">{label}</div>
          <div className="text-xs text-muted-foreground">
            {isComplete ? "Completed" : isCurrent ? "In Progress" : "Pending"}
          </div>
        </div>
        {isComplete && (
          <Badge variant="secondary" className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-100">
            ✓
          </Badge>
        )}
      </div>
    );
  };

  if (!projectId) {
    return <EmptyState message={DASHBOARD_TEXT.NO_PROJECT_SELECTED} />;
  }

  if (loading) {
    return <LoadingState />;
  }

  if (error) {
    return <ErrorState error={error} />;
  }

  if (!project) {
    return <ErrorState error="Project not found" />;
  }

  // Determine if analysis is complete
  const hasBasicAnalysis = !!project.last_risk_check_at;
  const hasFullAnalysis = project.mcstc_risk_score !== null && project.mcstc_risk_score !== undefined;

  return (
    <div className="space-y-6">
      {/* Project Header */}
      <ProjectHeader 
        project={project}
        branches={branches}
        selectedBranch={selectedBranch}
        onBranchChange={setSelectedBranch}
        onConfirmBranchSwitch={handleConfirmBranchSwitch}
        hasBasicAnalysis={hasBasicAnalysis}
        hasFullAnalysis={hasFullAnalysis}
        branchesCount={branches.length}
        isSwitchingBranch={isSwitchingBranch}
      />

      {/* Tabs Navigation */}
      <div className="border-b border-gray-200 dark:border-gray-700">
        <div className="flex gap-4">
          <button
            onClick={() => setActiveTab("workflow")}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === "workflow"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
          >
            Run Analysis
          </button>
          <button
            onClick={() => setActiveTab("analytics")}
            className={`px-4 py-2 font-medium border-b-2 transition-colors ${
              activeTab === "analytics"
                ? "border-primary text-primary"
                : "border-transparent text-muted-foreground hover:text-foreground"
            }`}
            disabled={!hasBasicAnalysis}
          >
            Analysis History
          </button>
        </div>
      </div>

      {/* Tab Content */}
      {activeTab === "workflow" && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left: Step Indicator */}
          <div className="space-y-3">
            <h3 className="text-lg font-semibold mb-4">Analysis Pipeline</h3>
            {renderStepIndicator("tnm", "1. TNM Analysis", <GitBranch className="h-5 w-5" />)}
            {renderStepIndicator("stc", "2. STC Calculation", <BarChart3 className="h-5 w-5" />)}
            {renderStepIndicator("classification", "3. Role Classification", <Users className="h-5 w-5" />)}
            {renderStepIndicator("mcstc", "4. MC-STC Analysis", <BarChart3 className="h-5 w-5" />)}
          </div>

          {/* Right: Current Step Details */}
          <div className="lg:col-span-2">
            {currentStep === "tnm" && (
              <Card>
                <div className="p-6 space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Step 1: TNM Analysis</h3>
                    <p className="text-muted-foreground">
                      Analyze repository structure and extract contributor information.
                    </p>
                  </div>

                  {/* Status Display */}
                  {!project.repository_path ? (
                    <Alert>
                      <Loader2 className="h-4 w-4 animate-spin" />
                      <AlertDescription>
                        TNM analysis is running... This may take several minutes.
                      </AlertDescription>
                    </Alert>
                  ) : (
                    <Alert className="border-green-500 bg-green-50 dark:bg-green-950/20">
                      <CheckCircle2 className="h-4 w-4 text-green-600" />
                      <AlertDescription className="text-green-700 dark:text-green-300">
                        TNM analysis completed! {project.members_count || 0} contributors found.
                      </AlertDescription>
                    </Alert>
                  )}

                  {/* Action Buttons */}
                  <div className="flex gap-4">
                    <Button
                      onClick={handleRunTNMAnalysis}
                      disabled={runningTNMAnalysis || !project.repository_path}
                      size="lg"
                    >
                      {runningTNMAnalysis ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Running...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="mr-2 h-4 w-4" />
                          Re-run TNM Analysis
                        </>
                      )}
                    </Button>
                    
                    {project.repository_path && (
                      <Button
                        onClick={() => setCurrentStep("stc")}
                        variant="outline"
                        size="lg"
                      >
                        Next: STC Analysis →
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}

            {currentStep === "stc" && (
              <Card>
                <div className="p-6 space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Step 2: STC Analysis</h3>
                    <p className="text-muted-foreground">
                      Calculate Socio-Technical Congruence to measure coordination alignment.
                    </p>
                  </div>

                  {analysisMessage && (
                    <Alert>
                      <AlertDescription>{analysisMessage}</AlertDescription>
                    </Alert>
                  )}

                  <div className="flex gap-4">
                    <Button
                      onClick={handleRunSTCAnalysis}
                      disabled={runningSTCAnalysis}
                      size="lg"
                    >
                      {runningSTCAnalysis ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Running STC...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="mr-2 h-4 w-4" />
                          Run STC Analysis
                        </>
                      )}
                    </Button>

                    {hasBasicAnalysis && (
                      <Button
                        onClick={() => setCurrentStep("classification")}
                        variant="outline"
                        size="lg"
                      >
                        Next: Role Classification →
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}

            {currentStep === "classification" && (
              <Card>
                <div className="p-6 space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Step 3: Contributors Classification</h3>
                    <p className="text-muted-foreground">
                      Assign functional roles to contributors for MC-STC analysis.
                    </p>
                  </div>

                  <ContributorRoleManagement projectId={projectId} />

                  <div className="flex justify-end gap-4 pt-4 border-t">
                    <Button
                      onClick={() => setCurrentStep("mcstc")}
                      size="lg"
                    >
                      Next: MC-STC Analysis →
                    </Button>
                  </div>
                </div>
              </Card>
            )}

            {currentStep === "mcstc" && (
              <Card>
                <div className="p-6 space-y-6">
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Step 4: MC-STC Analysis</h3>
                    <p className="text-muted-foreground">
                      Calculate Multi-Class STC based on contributor functional roles.
                    </p>
                  </div>

                  {analysisMessage && (
                    <Alert>
                      <AlertDescription>{analysisMessage}</AlertDescription>
                    </Alert>
                  )}

                  <Alert className="border-blue-500 bg-blue-50 dark:bg-blue-950/20">
                    <AlertCircle className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-700 dark:text-blue-300">
                      Make sure contributor roles are properly assigned before running MC-STC analysis.
                    </AlertDescription>
                  </Alert>

                  <div className="flex gap-4">
                    <Button
                      onClick={handleRunMCSTCAnalysis}
                      disabled={runningMCSTCAnalysis}
                      size="lg"
                    >
                      {runningMCSTCAnalysis ? (
                        <>
                          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                          Running MC-STC...
                        </>
                      ) : (
                        <>
                          <PlayCircle className="mr-2 h-4 w-4" />
                          Run MC-STC Analysis
                        </>
                      )}
                    </Button>

                    {hasFullAnalysis && (
                      <Button
                        onClick={() => setActiveTab("overview")}
                        variant="outline"
                        size="lg"
                      >
                        View Complete Results →
                      </Button>
                    )}
                  </div>
                </div>
              </Card>
            )}

            {currentStep === "complete" && (
              <Card>
                <div className="p-6 space-y-6 text-center">
                  <div className="text-6xl mb-4">🎉</div>
                  <div>
                    <h3 className="text-xl font-semibold mb-2">Analysis Complete!</h3>
                    <p className="text-muted-foreground">
                      All analysis steps have been completed successfully. View detailed history and charts in the Analysis History tab.
                    </p>
                  </div>

                  <Button
                    onClick={() => setActiveTab("analytics")}
                    size="lg"
                  >
                    View Analysis History →
                  </Button>
                </div>
              </Card>
            )}
          </div>
        </div>
      )}

      {activeTab === "analytics" && hasBasicAnalysis && (
        <div className="space-y-6">
          {/* Analytics History Timeline */}
          <AnalyticsHistory 
            projectId={projectId} 
            onViewDetails={handleViewDetails}
          />
          
          {/* Matrix Modal */}
          {showDetailsModal && (
            <CoordinationPairsModal
              stcId={selectedSTCId}
              mcstcId={selectedMCSTCId}
              branch={detailsBranch}
              open={showDetailsModal}
              onClose={handleCloseDetails}
            />
          )}

          {/* Current Branch Stats */}
          <ProjectCharts projectId={projectId} branchName={selectedBranch} />
        </div>
      )}
    </div>
  );
}
