export default function About() {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div className="max-w-3xl mx-auto">
        <h1 className="text-4xl font-bold text-primary-900 mb-8 animate-fade-in">
          About Resume Match AI
        </h1>

        <div className="prose prose-lg">
          <section className="mb-8 animate-slide-up">
            <h2 className="text-2xl font-semibold text-primary-900 mb-4">
              Our Mission
            </h2>
            <p className="text-primary-600 leading-relaxed">
              Resume Match AI is dedicated to revolutionizing the recruitment
              process by leveraging cutting-edge artificial intelligence
              technology. We help companies find the perfect candidates faster
              and more efficiently than ever before.
            </p>
          </section>

          <section
            className="mb-8 animate-slide-up"
            style={{ animationDelay: "0.1s" }}
          >
            <h2 className="text-2xl font-semibold text-primary-900 mb-4">
              What We Do
            </h2>
            <p className="text-primary-600 leading-relaxed mb-4">
              Our platform uses advanced AI algorithms to analyze resumes and
              job descriptions, providing intelligent matching scores and
              detailed insights. We help recruiters:
            </p>
            <ul className="list-disc list-inside text-primary-600 space-y-2 ml-4">
              <li>Automatically match candidates to job openings</li>
              <li>Identify skill gaps and strengths</li>
              <li>Schedule and manage interviews efficiently</li>
              <li>Make data-driven hiring decisions</li>
              <li>Reduce time-to-hire significantly</li>
            </ul>
          </section>

          <section
            className="mb-8 animate-slide-up"
            style={{ animationDelay: "0.2s" }}
          >
            <h2 className="text-2xl font-semibold text-primary-900 mb-4">
              Our Technology
            </h2>
            <p className="text-primary-600 leading-relaxed">
              Built with state-of-the-art machine learning models and natural
              language processing, our platform analyzes thousands of data
              points to provide accurate candidate-job matching. We continuously
              improve our algorithms to ensure the best results for our users.
            </p>
          </section>

          <section
            className="mb-8 animate-slide-up"
            style={{ animationDelay: "0.3s" }}
          >
            <h2 className="text-2xl font-semibold text-primary-900 mb-4">
              Why Choose Us
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="card bg-accent-50 border-accent-200">
                <h3 className="font-semibold text-primary-900 mb-2">
                  🎯 Accurate Matching
                </h3>
                <p className="text-primary-600 text-sm">
                  Our AI provides highly accurate candidate-job matching scores
                  based on skills, experience, and requirements.
                </p>
              </div>
              <div className="card bg-success-50 border-success-200">
                <h3 className="font-semibold text-primary-900 mb-2">
                  ⚡ Fast Processing
                </h3>
                <p className="text-primary-600 text-sm">
                  Process hundreds of resumes in minutes, not days. Get instant
                  results and insights.
                </p>
              </div>
              <div className="card bg-info-50 border-info-200">
                <h3 className="font-semibold text-primary-900 mb-2">
                  📊 Detailed Analytics
                </h3>
                <p className="text-primary-600 text-sm">
                  Comprehensive analytics and reporting to help you make
                  informed hiring decisions.
                </p>
              </div>
              <div className="card bg-warning-50 border-warning-200">
                <h3 className="font-semibold text-primary-900 mb-2">
                  🔒 Secure & Private
                </h3>
                <p className="text-primary-600 text-sm">
                  Your data is encrypted and secure. We take privacy and
                  security seriously.
                </p>
              </div>
            </div>
          </section>

          <section
            className="mb-8 animate-slide-up"
            style={{ animationDelay: "0.4s" }}
          >
            <h2 className="text-2xl font-semibold text-primary-900 mb-4">
              Get Started
            </h2>
            <p className="text-primary-600 leading-relaxed mb-4">
              Ready to transform your hiring process? Sign up today and
              experience the power of AI-driven recruitment.
            </p>
            <div className="flex gap-4">
              <a href="/auth/register" className="btn-accent">
                Get Started
              </a>
              <a href="/auth/login" className="btn-outline">
                Sign In
              </a>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
