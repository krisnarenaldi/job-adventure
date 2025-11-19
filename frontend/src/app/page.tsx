import Link from "next/link";

export default function Home() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="text-center animate-fade-in">
        <h1 className="text-4xl font-bold text-primary-900 sm:text-5xl md:text-6xl">
          AI-Powered Resume Matching
        </h1>
        <p className="mt-3 max-w-md mx-auto text-base text-primary-600 sm:text-lg md:mt-5 md:text-xl md:max-w-3xl">
          Streamline your hiring process with AI-powered resume analysis. Upload
          job descriptions and candidate resumes to get intelligent match
          scores, skill gap analysis, and detailed explanations to make better
          hiring decisions.
        </p>
        <div className="mt-5 max-w-md mx-auto sm:flex sm:justify-center md:mt-8 gap-4">
          <Link
            href="/recruiter"
            className="btn-accent w-full sm:w-auto flex items-center justify-center md:py-4 md:text-lg md:px-10"
          >
            Get Started
          </Link>
          <Link
            href="/auth/login"
            className="btn-outline w-full sm:w-auto flex items-center justify-center md:py-4 md:text-lg md:px-10 mt-3 sm:mt-0"
          >
            Sign In
          </Link>
        </div>
      </div>

      <div className="mt-16">
        <div className="grid grid-cols-1 gap-8 md:grid-cols-3">
          <div className="card-interactive text-center animate-slide-up">
            <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-accent-600 text-white mx-auto shadow-medium">
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
                  d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                />
              </svg>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-primary-900">
              Smart Document Processing
            </h3>
            <p className="mt-2 text-base text-primary-600">
              Upload job descriptions and candidate resumes in PDF or DOCX
              format. Our AI extracts and analyzes content automatically.
            </p>
          </div>

          <div
            className="card-interactive text-center animate-slide-up"
            style={{ animationDelay: "0.1s" }}
          >
            <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-accent-600 text-white mx-auto shadow-medium">
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
                  d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                />
              </svg>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-primary-900">
              Intelligent Candidate Ranking
            </h3>
            <p className="mt-2 text-base text-primary-600">
              Automatically rank candidates with precise match scores based on
              semantic similarity and comprehensive skill analysis.
            </p>
          </div>

          <div
            className="card-interactive text-center animate-slide-up"
            style={{ animationDelay: "0.2s" }}
          >
            <div className="flex items-center justify-center h-12 w-12 rounded-lg bg-accent-600 text-white mx-auto shadow-medium">
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
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
            </div>
            <h3 className="mt-4 text-lg font-semibold text-primary-900">
              Detailed Hiring Insights
            </h3>
            <p className="mt-2 text-base text-primary-600">
              Get comprehensive explanations for each match, including candidate
              strengths, skill gaps, and hiring recommendations.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
