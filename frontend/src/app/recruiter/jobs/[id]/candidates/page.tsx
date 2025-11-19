"use client";

import { useState, useEffect } from "react";
import { useParams } from "next/navigation";
import {
  apiClient,
  MatchResult,
  JobDescription,
  CandidateStatus,
  CandidateNote,
} from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { FileUpload } from "@/components/FileUpload";
import { InterviewScheduler } from "@/components/InterviewScheduler";

// Feature flag - set to true once database migration is applied
const STATUS_FEATURE_ENABLED = true;

export default function JobCandidates() {
  const params = useParams();
  const jobId = params.id as string;

  const [job, setJob] = useState<JobDescription | null>(null);
  const [matches, setMatches] = useState<MatchResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selectedMatch, setSelectedMatch] = useState<MatchResult | null>(null);
  const [statusFilter, setStatusFilter] = useState<CandidateStatus | "all">(
    "all"
  );
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(
    new Set()
  );
  const [candidateInfo, setCandidateInfo] = useState({
    name: "",
    email: "",
    phone: "",
  });
  const [showScheduler, setShowScheduler] = useState(false);
  const [notes, setNotes] = useState<CandidateNote[]>([]);
  const [loadingNotes, setLoadingNotes] = useState(false);
  const [noteText, setNoteText] = useState("");
  const [isPrivateNote, setIsPrivateNote] = useState(false);
  const [editingNoteId, setEditingNoteId] = useState<string | null>(null);
  const [editingNoteText, setEditingNoteText] = useState("");
  const [noteSearchQuery, setNoteSearchQuery] = useState("");
  const [currentUserId, setCurrentUserId] = useState<string | null>(null);
  const [showExportModal, setShowExportModal] = useState(false);
  const [exportFormat, setExportFormat] = useState<"csv" | "xlsx">("csv");
  const [exportFilters, setExportFilters] = useState({
    status: "" as CandidateStatus | "",
    minScore: "",
    maxScore: "",
  });
  const [exporting, setExporting] = useState(false);
  const [showShareModal, setShowShareModal] = useState(false);
  const [shareData, setShareData] = useState({
    recipientEmail: "",
    customMessage: "",
    expiresInDays: "7",
  });
  const [sharing, setSharing] = useState(false);
  const [shareUrl, setShareUrl] = useState<string | null>(null);
  const [updatingStatus, setUpdatingStatus] = useState<string | null>(null);

  useEffect(() => {
    loadJobAndMatches();
    loadCurrentUser();
  }, [jobId]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (selectedMatch) {
      loadNotes(selectedMatch.id);
    }
  }, [selectedMatch]); // eslint-disable-line react-hooks/exhaustive-deps

  // ESC key handler for modals
  useEffect(() => {
    const handleEscKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        if (showScheduler) {
          setShowScheduler(false);
        } else if (selectedMatch) {
          setSelectedMatch(null);
        } else if (showExportModal) {
          setShowExportModal(false);
        } else if (showShareModal) {
          closeShareModal();
        }
      }
    };

    document.addEventListener("keydown", handleEscKey);
    return () => document.removeEventListener("keydown", handleEscKey);
  }, [showScheduler, selectedMatch, showExportModal, showShareModal]); // eslint-disable-line react-hooks/exhaustive-deps

  const loadCurrentUser = async () => {
    const response = await apiClient.getCurrentUser();
    if (response.data) {
      setCurrentUserId(response.data.id);
    }
  };

  const loadNotes = async (matchId: string) => {
    setLoadingNotes(true);
    const response = await apiClient.getNotes(matchId);
    if (response.data) {
      setNotes(response.data);
    } else {
      setNotes([]);
    }
    setLoadingNotes(false);
  };

  const loadJobAndMatches = async () => {
    setLoading(true);

    // Load job details
    const jobResponse = await apiClient.getJob(jobId);
    if (jobResponse.error) {
      setError(jobResponse.error);
    } else {
      setJob(jobResponse.data || null);
    }

    // Load match results
    const matchResponse = await apiClient.getMatchResults(jobId);
    if (matchResponse.error) {
      // Don't show error for match results - just show empty state
      setMatches([]);
    } else {
      setMatches(matchResponse.data || []);
    }

    setLoading(false);
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setCandidateInfo((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleResumeUpload = async (file: File) => {
    // Check if job is inactive
    if (job && !job.is_active) {
      const confirmed = window.confirm(
        "This job is currently inactive. Candidates uploaded to inactive jobs will not be matched automatically. Do you want to continue?"
      );
      if (!confirmed) {
        return;
      }
    }

    // Validate candidate info
    if (!candidateInfo.name.trim()) {
      setError("Please enter candidate name");
      return;
    }
    if (!candidateInfo.email.trim()) {
      setError("Please enter candidate email");
      return;
    }

    // Check if candidate already exists
    const existingCandidate = matches.find(
      (m) =>
        m.candidate_email?.toLowerCase() === candidateInfo.email.toLowerCase()
    );
    if (existingCandidate) {
      setError(
        `A candidate with email ${candidateInfo.email} has already been added to this job.`
      );
      return;
    }

    setUploading(true);
    setError(null);

    try {
      // Upload resume with candidate information
      const uploadResponse = await apiClient.uploadResume(
        file,
        candidateInfo.name,
        candidateInfo.email,
        candidateInfo.phone || undefined,
        jobId
      );

      if (uploadResponse.error) {
        setError(uploadResponse.error);
        setUploading(false);
        return;
      }

      // Resume uploaded successfully - matching is done automatically
      if (uploadResponse.data) {
        // Clear form
        setCandidateInfo({ name: "", email: "", phone: "" });
        // Show success message
        setError(null);
        alert("Resume uploaded and analyzed successfully!");

        // Reload matches to show the new candidate
        await loadJobAndMatches();
      }
    } catch {
      setError("Failed to upload and process resume");
    }

    setUploading(false);
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return "text-green-600 bg-green-100";
    if (score >= 60) return "text-yellow-600 bg-yellow-100";
    return "text-red-600 bg-red-100";
  };

  const getStatusColor = (status?: CandidateStatus) => {
    switch (status) {
      case "shortlisted":
        return "bg-green-100 text-green-800 border-green-200";
      case "rejected":
        return "bg-red-100 text-red-800 border-red-200";
      case "maybe":
        return "bg-yellow-100 text-yellow-800 border-yellow-200";
      case "pending":
      default:
        return "bg-gray-100 text-gray-800 border-gray-200";
    }
  };

  const getStatusLabel = (status?: CandidateStatus) => {
    switch (status) {
      case "shortlisted":
        return "Shortlisted";
      case "rejected":
        return "Rejected";
      case "maybe":
        return "Maybe";
      case "pending":
      default:
        return "Pending";
    }
  };

  const handleStatusUpdate = async (
    matchId: string,
    newStatus: CandidateStatus
  ) => {
    setUpdatingStatus(matchId);
    setError(null);
    
    const response = await apiClient.updateMatchStatus(matchId, newStatus);
    if (response.error) {
      setError(response.error);
    } else {
      // Update the match in the local state
      setMatches((prevMatches) =>
        prevMatches.map((match) =>
          match.id === matchId ? { ...match, status: newStatus } : match
        )
      );
      // Update selected match if it's the one being updated
      if (selectedMatch?.id === matchId) {
        setSelectedMatch({ ...selectedMatch, status: newStatus });
      }
    }
    
    setUpdatingStatus(null);
  };

  const handleBulkStatusUpdate = async (newStatus: CandidateStatus) => {
    const updates = Array.from(selectedCandidates).map((matchId) =>
      apiClient.updateMatchStatus(matchId, newStatus)
    );

    await Promise.all(updates);

    // Reload matches to reflect changes
    await loadJobAndMatches();
    setSelectedCandidates(new Set());
  };

  const toggleCandidateSelection = (matchId: string) => {
    setSelectedCandidates((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(matchId)) {
        newSet.delete(matchId);
      } else {
        newSet.add(matchId);
      }
      return newSet;
    });
  };

  const filteredMatches =
    statusFilter === "all"
      ? matches
      : matches.filter((match) => (match.status || "pending") === statusFilter);

  const handleAddNote = async () => {
    if (!selectedMatch || !noteText.trim()) return;

    const response = await apiClient.createNote({
      match_id: selectedMatch.id,
      note_text: noteText.trim(),
      is_private: isPrivateNote,
    });

    if (response.data) {
      setNotes([response.data, ...notes]);
      setNoteText("");
      setIsPrivateNote(false);
    } else if (response.error) {
      alert(`Failed to add note: ${response.error}`);
    }
  };

  const handleUpdateNote = async (noteId: string) => {
    if (!editingNoteText.trim()) return;

    const response = await apiClient.updateNote(noteId, {
      note_text: editingNoteText.trim(),
    });

    if (response.data) {
      setNotes(
        notes.map((note) => (note.id === noteId ? response.data! : note))
      );
      setEditingNoteId(null);
      setEditingNoteText("");
    } else if (response.error) {
      alert(`Failed to update note: ${response.error}`);
    }
  };

  const handleDeleteNote = async (noteId: string) => {
    if (!confirm("Are you sure you want to delete this note?")) return;

    const response = await apiClient.deleteNote(noteId);
    if (!response.error) {
      setNotes(notes.filter((note) => note.id !== noteId));
    } else {
      alert(`Failed to delete note: ${response.error}`);
    }
  };

  const startEditingNote = (note: CandidateNote) => {
    setEditingNoteId(note.id);
    setEditingNoteText(note.note_text);
  };

  const cancelEditingNote = () => {
    setEditingNoteId(null);
    setEditingNoteText("");
  };

  const filteredNotes = noteSearchQuery.trim()
    ? notes.filter(
        (note) =>
          note.note_text
            .toLowerCase()
            .includes(noteSearchQuery.toLowerCase()) ||
          note.author_name
            ?.toLowerCase()
            .includes(noteSearchQuery.toLowerCase())
      )
    : notes;

  const formatNoteDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return "Just now";
    if (diffMins < 60)
      return `${diffMins} minute${diffMins > 1 ? "s" : ""} ago`;
    if (diffHours < 24)
      return `${diffHours} hour${diffHours > 1 ? "s" : ""} ago`;
    if (diffDays < 7) return `${diffDays} day${diffDays > 1 ? "s" : ""} ago`;

    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: date.getFullYear() !== now.getFullYear() ? "numeric" : undefined,
    });
  };

  const handleExport = async () => {
    setExporting(true);

    const filters: {
      status?: CandidateStatus;
      minScore?: number;
      maxScore?: number;
    } = {};

    if (exportFilters.status) {
      filters.status = exportFilters.status as CandidateStatus;
    }
    if (exportFilters.minScore) {
      filters.minScore = parseFloat(exportFilters.minScore);
    }
    if (exportFilters.maxScore) {
      filters.maxScore = parseFloat(exportFilters.maxScore);
    }

    const blob = await apiClient.exportCandidates(jobId, exportFormat, filters);

    if (blob) {
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      const timestamp = new Date()
        .toISOString()
        .replace(/[:.]/g, "-")
        .slice(0, -5);
      a.download = `${job?.title.replace(
        /\s+/g,
        "_"
      )}_candidates_${timestamp}.${exportFormat}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(url);

      setShowExportModal(false);
      setExportFilters({ status: "", minScore: "", maxScore: "" });
    } else {
      setError("Failed to export candidates. Please try again.");
    }

    setExporting(false);
  };

  const handleShare = async () => {
    setSharing(true);

    const response = await apiClient.createSharedLink({
      job_id: jobId,
      recipient_email: shareData.recipientEmail || undefined,
      custom_message: shareData.customMessage || undefined,
      expires_in_days: shareData.expiresInDays
        ? parseInt(shareData.expiresInDays)
        : undefined,
    });

    if (response.data) {
      setShareUrl(response.data.share_url || null);
      if (!shareData.recipientEmail) {
        // If no email, show the URL immediately
        alert(
          `Share link created! Copy the URL to share:\n${response.data.share_url}`
        );
      } else {
        alert(`Share link created and sent to ${shareData.recipientEmail}!`);
      }
    } else {
      setError(response.error || "Failed to create share link");
    }

    setSharing(false);
  };

  const copyShareUrl = () => {
    if (shareUrl) {
      navigator.clipboard.writeText(shareUrl);
      alert("Share URL copied to clipboard!");
    }
  };

  const closeShareModal = () => {
    setShowShareModal(false);
    setShareData({ recipientEmail: "", customMessage: "", expiresInDays: "7" });
    setShareUrl(null);
  };

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="flex justify-center">
          <LoadingSpinner size="lg" />
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            {job?.title} - Candidates
          </h1>
          <p className="mt-1 text-sm text-gray-500">
            {job?.company} • {matches.length} candidates
          </p>
        </div>
      </div>

      {error && (
        <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
          <div className="flex">
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Upload Section */}
        <div className="lg:col-span-1">
          <div className="bg-white shadow rounded-lg p-6">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Add Candidate
            </h3>

            {/* Inactive Job Warning */}
            {job && !job.is_active && (
              <div className="mb-4 bg-yellow-50 border border-yellow-200 rounded-md p-4">
                <div className="flex">
                  <div className="flex-shrink-0">
                    <svg
                      className="h-5 w-5 text-yellow-400"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                  <div className="ml-3">
                    <h3 className="text-sm font-medium text-yellow-800">
                      Job is Inactive
                    </h3>
                    <div className="mt-1 text-sm text-yellow-700">
                      <p>
                        This job is currently inactive. Uploaded resumes will
                        not be automatically matched.
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            )}

            <div className="space-y-4 mb-6">
              <div>
                <label
                  htmlFor="name"
                  className="block text-sm font-semibold text-gray-900 mb-2"
                >
                  Candidate Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="name"
                  name="name"
                  value={candidateInfo.name}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2.5 text-gray-900 bg-white border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="John Doe"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-semibold text-gray-900 mb-2"
                >
                  Email Address <span className="text-red-500">*</span>
                </label>
                <input
                  type="email"
                  id="email"
                  name="email"
                  value={candidateInfo.email}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2.5 text-gray-900 bg-white border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="john@example.com"
                  required
                />
              </div>

              <div>
                <label
                  htmlFor="phone"
                  className="block text-sm font-semibold text-gray-900 mb-2"
                >
                  Phone Number{" "}
                  <span className="text-gray-500 font-normal">(optional)</span>
                </label>
                <input
                  type="tel"
                  id="phone"
                  name="phone"
                  value={candidateInfo.phone}
                  onChange={handleInputChange}
                  className="w-full px-4 py-2.5 text-gray-900 bg-white border-2 border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 transition-colors"
                  placeholder="+1 (555) 123-4567"
                />
              </div>
            </div>

            <div className="border-t-2 border-gray-200 pt-6 mt-2">
              <label className="block text-sm font-semibold text-gray-900 mb-3">
                Upload Resume <span className="text-red-500">*</span>
              </label>
              <FileUpload
                onFileSelect={handleResumeUpload}
                accept=".pdf,.docx"
                maxSize={10}
              />
            </div>

            {uploading && (
              <div className="mt-4 flex items-center">
                <LoadingSpinner size="sm" className="mr-2" />
                <span className="text-sm text-gray-600">
                  Processing resume...
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Candidates List */}
        <div className="lg:col-span-2">
          <div className="bg-white shadow rounded-lg">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between mb-4">
                <h3 className="text-lg font-medium text-gray-900">
                  Candidate Rankings
                </h3>
                {matches.length > 0 && (
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowShareModal(true)}
                      className="inline-flex items-center px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      <svg
                        className="h-4 w-4 mr-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                        />
                      </svg>
                      Share
                    </button>
                    <button
                      onClick={() => setShowExportModal(true)}
                      className="inline-flex items-center px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      <svg
                        className="h-4 w-4 mr-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      Export
                    </button>
                  </div>
                )}
              </div>

              {/* Status Filter - Only show if feature is enabled */}
              {STATUS_FEATURE_ENABLED && (
                <div className="flex flex-wrap gap-2 mb-4">
                  <button
                    onClick={() => setStatusFilter("all")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === "all"
                        ? "bg-blue-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    All ({matches.length})
                  </button>
                  <button
                    onClick={() => setStatusFilter("pending")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === "pending"
                        ? "bg-gray-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    Pending (
                    {
                      matches.filter(
                        (m) => (m.status || "pending") === "pending"
                      ).length
                    }
                    )
                  </button>
                  <button
                    onClick={() => setStatusFilter("shortlisted")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === "shortlisted"
                        ? "bg-green-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    Shortlisted (
                    {matches.filter((m) => m.status === "shortlisted").length})
                  </button>
                  <button
                    onClick={() => setStatusFilter("maybe")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === "maybe"
                        ? "bg-yellow-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    Maybe ({matches.filter((m) => m.status === "maybe").length})
                  </button>
                  <button
                    onClick={() => setStatusFilter("rejected")}
                    className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                      statusFilter === "rejected"
                        ? "bg-red-600 text-white"
                        : "bg-gray-100 text-gray-700 hover:bg-gray-200"
                    }`}
                  >
                    Rejected (
                    {matches.filter((m) => m.status === "rejected").length})
                  </button>
                </div>
              )}

              {/* Bulk Actions - Only show if feature is enabled */}
              {STATUS_FEATURE_ENABLED && selectedCandidates.size > 0 && (
                <div className="flex items-center gap-2 p-3 bg-blue-50 rounded-lg border border-blue-200">
                  <span className="text-sm font-medium text-blue-900">
                    {selectedCandidates.size} selected
                  </span>
                  <div className="flex gap-2 ml-auto">
                    <button
                      onClick={() => handleBulkStatusUpdate("shortlisted")}
                      className="px-3 py-1 text-xs font-medium text-green-700 bg-green-100 rounded hover:bg-green-200"
                    >
                      Shortlist
                    </button>
                    <button
                      onClick={() => handleBulkStatusUpdate("maybe")}
                      className="px-3 py-1 text-xs font-medium text-yellow-700 bg-yellow-100 rounded hover:bg-yellow-200"
                    >
                      Maybe
                    </button>
                    <button
                      onClick={() => handleBulkStatusUpdate("rejected")}
                      className="px-3 py-1 text-xs font-medium text-red-700 bg-red-100 rounded hover:bg-red-200"
                    >
                      Reject
                    </button>
                    <button
                      onClick={() => setSelectedCandidates(new Set())}
                      className="px-3 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded hover:bg-gray-200"
                    >
                      Clear
                    </button>
                  </div>
                </div>
              )}
            </div>

            {filteredMatches.length === 0 ? (
              <div className="p-6 text-center">
                <p className="text-gray-500">
                  {matches.length === 0
                    ? "No candidates yet. Upload resumes to get started."
                    : `No ${statusFilter} candidates.`}
                </p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200">
                {filteredMatches
                  .sort((a, b) => b.match_score - a.match_score)
                  .map((match, index) => (
                    <div key={match.id} className="p-6 hover:bg-gray-50">
                      <div className="flex items-start gap-4">
                        {/* Checkbox - Only show if feature is enabled */}
                        {STATUS_FEATURE_ENABLED && (
                          <input
                            type="checkbox"
                            checked={selectedCandidates.has(match.id)}
                            onChange={(e) => {
                              e.stopPropagation();
                              toggleCandidateSelection(match.id);
                            }}
                            className="mt-1 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                          />
                        )}

                        {/* Candidate Info */}
                        <div
                          className="flex-1 cursor-pointer"
                          onClick={() => setSelectedMatch(match)}
                        >
                          <div className="flex items-center justify-between">
                            <div className="flex items-center">
                              <div className="flex-shrink-0">
                                <div className="h-10 w-10 rounded-full bg-gray-300 flex items-center justify-center">
                                  <span className="text-gray-600 font-medium text-sm">
                                    #{index + 1}
                                  </span>
                                </div>
                              </div>
                              <div className="ml-4">
                                <h4 className="text-lg font-medium text-gray-900">
                                  {match.candidate_name || "Unknown Candidate"}
                                </h4>
                                <p className="text-sm text-gray-500">
                                  {match.candidate_email}
                                </p>
                              </div>
                            </div>
                            <div className="flex items-center space-x-3">
                              <span
                                className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getScoreColor(
                                  match.match_score
                                )}`}
                              >
                                {Math.round(match.match_score)}% Match
                              </span>
                              {/* Status Badge - Only show if feature is enabled */}
                              {STATUS_FEATURE_ENABLED && (
                                <span
                                  className={`inline-flex items-center px-2.5 py-0.5 rounded-lg text-xs font-medium border ${getStatusColor(
                                    match.status || "pending"
                                  )}`}
                                >
                                  {getStatusLabel(match.status || "pending")}
                                </span>
                              )}
                            </div>
                          </div>

                          <div className="mt-4">
                            <div className="flex flex-wrap gap-2">
                              {match.key_strengths
                                .slice(0, 3)
                                .map((strength, idx) => (
                                  <span
                                    key={idx}
                                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-green-100 text-green-800"
                                  >
                                    {strength}
                                  </span>
                                ))}
                              {match.missing_skills
                                .slice(0, 2)
                                .map((skill, idx) => (
                                  <span
                                    key={idx}
                                    className="inline-flex items-center px-2 py-1 rounded-md text-xs font-medium bg-red-100 text-red-800"
                                  >
                                    Missing: {skill}
                                  </span>
                                ))}
                            </div>
                          </div>
                        </div>

                        {/* Status Dropdown - Only show if feature is enabled */}
                        {STATUS_FEATURE_ENABLED && (
                          <div
                            className="relative"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <select
                              value={match.status || "pending"}
                              onChange={(e) =>
                                handleStatusUpdate(
                                  match.id,
                                  e.target.value as CandidateStatus
                                )
                              }
                              disabled={updatingStatus === match.id}
                              className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
                            >
                              <option value="pending">Pending</option>
                              <option value="shortlisted">Shortlisted</option>
                              <option value="maybe">Maybe</option>
                              <option value="rejected">Rejected</option>
                            </select>
                            {updatingStatus === match.id && (
                              <div className="absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none">
                                <LoadingSpinner size="sm" />
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Match Details Modal */}
      {selectedMatch && (
        <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
          <div className="relative w-full max-w-3xl bg-white rounded-xl shadow-2xl max-h-[90vh] overflow-y-auto">
            {/* Header */}
            <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
              <div className="flex justify-between items-start">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-2xl font-bold text-gray-900">
                      {selectedMatch.candidate_name || "Unknown Candidate"}
                    </h3>
                    {/* Status Badge - Only show if feature is enabled */}
                    {STATUS_FEATURE_ENABLED && (
                      <span
                        className={`inline-flex items-center px-3 py-1 rounded-lg text-sm font-medium border ${getStatusColor(
                          selectedMatch.status || "pending"
                        )}`}
                      >
                        {getStatusLabel(selectedMatch.status || "pending")}
                      </span>
                    )}
                  </div>
                  <p className="text-sm text-gray-500 mt-1">
                    {selectedMatch.candidate_email}
                  </p>
                  
                </div>
                <button
                  onClick={() => setSelectedMatch(null)}
                  className="text-gray-400 hover:text-gray-600 transition-colors p-1 hover:bg-gray-100 rounded-lg"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-6 space-y-6">
              {/* Match Score */}
              <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600 mb-1">
                      Overall Match Score
                    </p>
                    <p className="text-3xl font-bold text-gray-900">
                      {Math.round(selectedMatch.match_score)}%
                    </p>
                  </div>
                  <div
                    className={`h-16 w-16 rounded-full flex items-center justify-center ${getScoreColor(
                      selectedMatch.match_score
                    )}`}
                  >
                    <svg
                      className="h-8 w-8"
                      fill="currentColor"
                      viewBox="0 0 20 20"
                    >
                      <path
                        fillRule="evenodd"
                        d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                        clipRule="evenodd"
                      />
                    </svg>
                  </div>
                </div>
              </div>

              {/* Match Analysis */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg
                    className="h-5 w-5 mr-2 text-blue-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                    />
                  </svg>
                  Match Analysis
                </h4>
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200">
                  <div className="prose prose-sm max-w-none text-gray-700">
                    {selectedMatch.explanation
                      .split("\n")
                      .map((paragraph, idx) => {
                        // Check if line starts with **
                        const headingMatch = paragraph.match(/^\*\*(.+?)\*\*/);
                        if (headingMatch) {
                          return (
                            <h5
                              key={idx}
                              className="text-base font-semibold text-gray-900 mt-4 mb-2 first:mt-0"
                            >
                              {headingMatch[1]}
                            </h5>
                          );
                        }
                        // Regular paragraph
                        if (paragraph.trim()) {
                          return (
                            <p key={idx} className="mb-2 leading-relaxed">
                              {paragraph}
                            </p>
                          );
                        }
                        return null;
                      })}
                  </div>
                  {selectedMatch.explanation.includes("*Note:") && (
                    <div className="mt-4 pt-4 border-t border-gray-300">
                      <div className="flex items-start space-x-2 text-xs text-gray-500">
                        <svg
                          className="h-4 w-4 mt-0.5 flex-shrink-0"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                            clipRule="evenodd"
                          />
                        </svg>
                        <p>
                          This analysis uses template-based matching. Enhanced
                          AI-powered insights from Claude will be available when
                          the Anthropic API service is properly configured.
                        </p>
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Key Strengths */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg
                    className="h-5 w-5 mr-2 text-green-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                  Key Strengths
                </h4>
                {selectedMatch.key_strengths.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedMatch.key_strengths.map((strength, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-green-100 text-green-800 border border-green-200"
                      >
                        <svg
                          className="h-4 w-4 mr-1.5"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"
                            clipRule="evenodd"
                          />
                        </svg>
                        {strength}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">
                    No key strengths identified
                  </p>
                )}
              </div>

              {/* Missing Skills */}
              <div>
                <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg
                    className="h-5 w-5 mr-2 text-red-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
                    />
                  </svg>
                  Areas for Development
                </h4>
                {selectedMatch.missing_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-2">
                    {selectedMatch.missing_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="inline-flex items-center px-3 py-1.5 rounded-lg text-sm font-medium bg-red-100 text-red-800 border border-red-200"
                      >
                        <svg
                          className="h-4 w-4 mr-1.5"
                          fill="currentColor"
                          viewBox="0 0 20 20"
                        >
                          <path
                            fillRule="evenodd"
                            d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z"
                            clipRule="evenodd"
                          />
                        </svg>
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic">
                    No missing skills identified
                  </p>
                )}
              </div>

              {/* Notes Section */}
              <div className="border-t border-gray-200 pt-6">
                <h4 className="text-lg font-semibold text-gray-900 mb-3 flex items-center">
                  <svg
                    className="h-5 w-5 mr-2 text-purple-600"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                    />
                  </svg>
                  Notes & Comments
                </h4>

                {/* Add Note Form */}
                <div className="bg-gray-50 rounded-lg p-4 border border-gray-200 mb-4">
                  <textarea
                    value={noteText}
                    onChange={(e) => setNoteText(e.target.value)}
                    placeholder="Add a note about this candidate..."
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none"
                    rows={3}
                  />
                  <div className="flex items-center justify-between mt-3">
                    <label className="flex items-center text-sm text-gray-700">
                      <input
                        type="checkbox"
                        checked={isPrivateNote}
                        onChange={(e) => setIsPrivateNote(e.target.checked)}
                        className="mr-2 h-4 w-4 text-blue-600 rounded border-gray-300 focus:ring-blue-500"
                      />
                      Private note (only visible to you)
                    </label>
                    <button
                      onClick={handleAddNote}
                      disabled={!noteText.trim()}
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      Add Note
                    </button>
                  </div>
                </div>

                {/* Notes Search */}
                {notes.length > 0 && (
                  <div className="mb-4">
                    <input
                      type="text"
                      value={noteSearchQuery}
                      onChange={(e) => setNoteSearchQuery(e.target.value)}
                      placeholder="Search notes..."
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm"
                    />
                  </div>
                )}

                {/* Notes List */}
                {loadingNotes ? (
                  <div className="flex justify-center py-4">
                    <LoadingSpinner size="sm" />
                  </div>
                ) : filteredNotes.length > 0 ? (
                  <div className="space-y-3 max-h-96 overflow-y-auto">
                    {filteredNotes.map((note) => (
                      <div
                        key={note.id}
                        className="bg-white rounded-lg p-4 border border-gray-200 hover:border-gray-300 transition-colors"
                      >
                        <div className="flex items-start justify-between mb-2">
                          <div className="flex items-center gap-2">
                            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
                              <span className="text-blue-600 font-medium text-sm">
                                {note.author_name?.charAt(0).toUpperCase() ||
                                  "?"}
                              </span>
                            </div>
                            <div>
                              <p className="text-sm font-medium text-gray-900">
                                {note.author_name || "Unknown"}
                              </p>
                              <p className="text-xs text-gray-500">
                                {formatNoteDate(note.created_at)}
                              </p>
                            </div>
                            {note.is_private && (
                              <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-yellow-100 text-yellow-800">
                                <svg
                                  className="h-3 w-3 mr-1"
                                  fill="currentColor"
                                  viewBox="0 0 20 20"
                                >
                                  <path
                                    fillRule="evenodd"
                                    d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z"
                                    clipRule="evenodd"
                                  />
                                </svg>
                                Private
                              </span>
                            )}
                          </div>
                          {note.user_id === currentUserId && (
                            <div className="flex gap-2">
                              {editingNoteId === note.id ? (
                                <>
                                  <button
                                    onClick={() => handleUpdateNote(note.id)}
                                    className="text-green-600 hover:text-green-700 text-sm font-medium"
                                  >
                                    Save
                                  </button>
                                  <button
                                    onClick={cancelEditingNote}
                                    className="text-gray-600 hover:text-gray-700 text-sm font-medium"
                                  >
                                    Cancel
                                  </button>
                                </>
                              ) : (
                                <>
                                  <button
                                    onClick={() => startEditingNote(note)}
                                    className="text-blue-600 hover:text-blue-700 text-sm font-medium"
                                  >
                                    Edit
                                  </button>
                                  <button
                                    onClick={() => handleDeleteNote(note.id)}
                                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                                  >
                                    Delete
                                  </button>
                                </>
                              )}
                            </div>
                          )}
                        </div>
                        {editingNoteId === note.id ? (
                          <textarea
                            value={editingNoteText}
                            onChange={(e) => setEditingNoteText(e.target.value)}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 resize-none text-sm"
                            rows={3}
                          />
                        ) : (
                          <p className="text-sm text-gray-700 whitespace-pre-wrap">
                            {note.note_text}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-gray-500 italic text-center py-4">
                    {noteSearchQuery.trim()
                      ? "No notes match your search"
                      : "No notes yet. Add the first note above."}
                  </p>
                )}
              </div>
            </div>

            {/* Footer */}
            <div className="sticky bottom-0 bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-xl">
              <div className="flex gap-3">
                <button
                  onClick={() => {
                    setShowScheduler(true);
                  }}
                  disabled={selectedMatch.status === "rejected"}
                  title={
                    selectedMatch.status === "rejected"
                      ? "Cannot schedule interviews for rejected candidates"
                      : "Schedule an interview"
                  }
                  className="flex-1 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 disabled:cursor-not-allowed text-white font-medium py-2.5 px-4 rounded-lg transition-colors flex items-center justify-center"
                >
                  <svg
                    className="h-5 w-5 mr-2"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                    />
                  </svg>
                  Schedule Interview
                </button>
                <button
                  onClick={() => setSelectedMatch(null)}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors"
                >
                  Close
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Interview Scheduler */}
      {showScheduler && selectedMatch && (
        <InterviewScheduler
          matchResultId={selectedMatch.id}
          jobId={jobId}
          candidateName={selectedMatch.candidate_name || "Candidate"}
          onSuccess={() => {
            setShowScheduler(false);
            setSelectedMatch(null);
            loadJobAndMatches();
          }}
          onCancel={() => setShowScheduler(false)}
        />
      )}

      {/* Export Modal */}
      {showExportModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
          <div className="relative w-full max-w-md bg-white rounded-xl shadow-2xl">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">
                  Export Candidates
                </h3>
                <button
                  onClick={() => setShowExportModal(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors p-1 hover:bg-gray-100 rounded-lg"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-6 space-y-4">
              {/* Format Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Export Format
                </label>
                <div className="flex gap-3">
                  <button
                    onClick={() => setExportFormat("csv")}
                    className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
                      exportFormat === "csv"
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
                    }`}
                  >
                    <div className="font-medium">CSV</div>
                    <div className="text-xs mt-1">Comma-separated values</div>
                  </button>
                  <button
                    onClick={() => setExportFormat("xlsx")}
                    className={`flex-1 px-4 py-3 rounded-lg border-2 transition-colors ${
                      exportFormat === "xlsx"
                        ? "border-blue-600 bg-blue-50 text-blue-700"
                        : "border-gray-300 bg-white text-gray-700 hover:border-gray-400"
                    }`}
                  >
                    <div className="font-medium">Excel</div>
                    <div className="text-xs mt-1">Microsoft Excel format</div>
                  </button>
                </div>
              </div>

              {/* Filters */}
              <div className="border-t border-gray-200 pt-4">
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Filters (Optional)
                </h4>

                {/* Status Filter */}
                {STATUS_FEATURE_ENABLED && (
                  <div className="mb-3">
                    <label className="block text-sm text-gray-600 mb-1">
                      Status
                    </label>
                    <select
                      value={exportFilters.status}
                      onChange={(e) =>
                        setExportFilters({
                          ...exportFilters,
                          status: e.target.value as CandidateStatus | "",
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">All Statuses</option>
                      <option value="pending">Pending</option>
                      <option value="shortlisted">Shortlisted</option>
                      <option value="maybe">Maybe</option>
                      <option value="rejected">Rejected</option>
                    </select>
                  </div>
                )}

                {/* Score Range */}
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">
                      Min Score (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={exportFilters.minScore}
                      onChange={(e) =>
                        setExportFilters({
                          ...exportFilters,
                          minScore: e.target.value,
                        })
                      }
                      placeholder="0"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                  <div>
                    <label className="block text-sm text-gray-600 mb-1">
                      Max Score (%)
                    </label>
                    <input
                      type="number"
                      min="0"
                      max="100"
                      value={exportFilters.maxScore}
                      onChange={(e) =>
                        setExportFilters({
                          ...exportFilters,
                          maxScore: e.target.value,
                        })
                      }
                      placeholder="100"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Export Info */}
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
                <div className="flex items-start">
                  <svg
                    className="h-5 w-5 text-blue-600 mt-0.5 mr-2 flex-shrink-0"
                    fill="currentColor"
                    viewBox="0 0 20 20"
                  >
                    <path
                      fillRule="evenodd"
                      d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                      clipRule="evenodd"
                    />
                  </svg>
                  <div className="text-sm text-blue-800">
                    <p className="font-medium mb-1">Export includes:</p>
                    <ul className="list-disc list-inside space-y-0.5 text-xs">
                      <li>Candidate name, email, and phone</li>
                      <li>Match score and status</li>
                      <li>Key strengths and missing skills</li>
                      <li>Application date</li>
                    </ul>
                  </div>
                </div>
              </div>
            </div>

            {/* Footer */}
            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-xl">
              <div className="flex gap-3">
                <button
                  onClick={() => setShowExportModal(false)}
                  disabled={exporting}
                  className="flex-1 bg-white hover:bg-gray-50 text-gray-700 font-medium py-2.5 px-4 rounded-lg border border-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Cancel
                </button>
                <button
                  onClick={handleExport}
                  disabled={exporting}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                >
                  {exporting ? (
                    <>
                      <LoadingSpinner size="sm" className="mr-2" />
                      Exporting...
                    </>
                  ) : (
                    <>
                      <svg
                        className="h-5 w-5 mr-2"
                        fill="none"
                        viewBox="0 0 24 24"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      Export
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Share Modal */}
      {showShareModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 overflow-y-auto h-full w-full z-50 flex items-center justify-center p-4">
          <div className="relative w-full max-w-md bg-white rounded-xl shadow-2xl">
            {/* Header */}
            <div className="bg-white border-b border-gray-200 px-6 py-4 rounded-t-xl">
              <div className="flex justify-between items-center">
                <h3 className="text-xl font-bold text-gray-900">
                  Share Candidates
                </h3>
                <button
                  onClick={closeShareModal}
                  className="text-gray-400 hover:text-gray-600 transition-colors p-1 hover:bg-gray-100 rounded-lg"
                >
                  <svg
                    className="h-6 w-6"
                    fill="none"
                    viewBox="0 0 24 24"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M6 18L18 6M6 6l12 12"
                    />
                  </svg>
                </button>
              </div>
            </div>

            {/* Content */}
            <div className="px-6 py-6 space-y-4">
              {!shareUrl ? (
                <>
                  {/* Recipient Email */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Recipient Email (Optional)
                    </label>
                    <input
                      type="email"
                      value={shareData.recipientEmail}
                      onChange={(e) =>
                        setShareData({
                          ...shareData,
                          recipientEmail: e.target.value,
                        })
                      }
                      placeholder="hiring.manager@company.com"
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      Leave empty to get a shareable link without sending an
                      email
                    </p>
                  </div>

                  {/* Custom Message */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Custom Message (Optional)
                    </label>
                    <textarea
                      value={shareData.customMessage}
                      onChange={(e) =>
                        setShareData({
                          ...shareData,
                          customMessage: e.target.value,
                        })
                      }
                      placeholder="Add a personal message..."
                      rows={3}
                      maxLength={1000}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500 resize-none"
                    />
                    <p className="text-xs text-gray-500 mt-1">
                      {shareData.customMessage.length}/1000 characters
                    </p>
                  </div>

                  {/* Expiration */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Link Expires In
                    </label>
                    <select
                      value={shareData.expiresInDays}
                      onChange={(e) =>
                        setShareData({
                          ...shareData,
                          expiresInDays: e.target.value,
                        })
                      }
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-green-500"
                    >
                      <option value="">Never</option>
                      <option value="1">1 day</option>
                      <option value="7">7 days</option>
                      <option value="14">14 days</option>
                      <option value="30">30 days</option>
                      <option value="90">90 days</option>
                    </select>
                  </div>

                  {/* Info Box */}
                  <div className="bg-green-50 border border-green-200 rounded-lg p-3">
                    <div className="flex items-start">
                      <svg
                        className="h-5 w-5 text-green-600 mt-0.5 mr-2 flex-shrink-0"
                        fill="currentColor"
                        viewBox="0 0 20 20"
                      >
                        <path
                          fillRule="evenodd"
                          d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z"
                          clipRule="evenodd"
                        />
                      </svg>
                      <div className="text-sm text-green-800">
                        <p className="font-medium mb-1">
                          Shared view includes:
                        </p>
                        <ul className="list-disc list-inside space-y-0.5 text-xs">
                          <li>Candidate rankings and match scores</li>
                          <li>Key strengths and missing skills</li>
                          <li>View-only access (no contact info)</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </>
              ) : (
                /* Share URL Display */
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Share URL
                  </label>
                  <div className="flex gap-2">
                    <input
                      type="text"
                      value={shareUrl}
                      readOnly
                      className="flex-1 px-3 py-2 border border-gray-300 rounded-lg bg-gray-50 text-sm"
                    />
                    <button
                      onClick={copyShareUrl}
                      className="px-4 py-2 bg-green-600 hover:bg-green-700 text-white text-sm font-medium rounded-lg transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                  <p className="text-xs text-gray-500 mt-2">
                    Share this URL with anyone you want to give access to the
                    candidate rankings.
                  </p>
                </div>
              )}
            </div>

            {/* Footer */}
            <div className="bg-gray-50 border-t border-gray-200 px-6 py-4 rounded-b-xl">
              <div className="flex gap-3">
                <button
                  onClick={closeShareModal}
                  disabled={sharing}
                  className="flex-1 bg-white hover:bg-gray-50 text-gray-700 font-medium py-2.5 px-4 rounded-lg border border-gray-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {shareUrl ? "Close" : "Cancel"}
                </button>
                {!shareUrl && (
                  <button
                    onClick={handleShare}
                    disabled={sharing}
                    className="flex-1 bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 px-4 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center"
                  >
                    {sharing ? (
                      <>
                        <LoadingSpinner size="sm" className="mr-2" />
                        Creating...
                      </>
                    ) : (
                      <>
                        <svg
                          className="h-5 w-5 mr-2"
                          fill="none"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path
                            strokeLinecap="round"
                            strokeLinejoin="round"
                            strokeWidth={2}
                            d="M8.684 13.342C8.886 12.938 9 12.482 9 12c0-.482-.114-.938-.316-1.342m0 2.684a3 3 0 110-2.684m0 2.684l6.632 3.316m-6.632-6l6.632-3.316m0 0a3 3 0 105.367-2.684 3 3 0 00-5.367 2.684zm0 9.316a3 3 0 105.368 2.684 3 3 0 00-5.368-2.684z"
                          />
                        </svg>
                        Create Share Link
                      </>
                    )}
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Interview Scheduler Modal */}
      {showScheduler && selectedMatch && (
        <InterviewScheduler
          matchResultId={selectedMatch.id}
          jobId={jobId}
          candidateName={selectedMatch.candidate_name || "Unknown Candidate"}
          onSuccess={() => {
            setShowScheduler(false);
            alert("Interview scheduled successfully!");
          }}
          onCancel={() => setShowScheduler(false)}
        />
      )}
    </div>
  );
}
