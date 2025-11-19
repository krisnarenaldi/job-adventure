"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { FileUpload } from "@/components/FileUpload";

export default function ContactPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [userEmail, setUserEmail] = useState<string>("");
  const [formData, setFormData] = useState({
    email: "",
    description: "",
  });
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  useEffect(() => {
    // Check authentication
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    // Fetch user info to pre-fill email
    const fetchUserInfo = async () => {
      try {
        const response = await apiClient.getCurrentUser();
        if (response.data) {
          const email = response.data.email;
          setUserEmail(email);
          setFormData((prev) => ({ ...prev, email }));
        }
      } catch (err) {
        console.error("Failed to fetch user info:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchUserInfo();
  }, [router]);

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setError(null);

    // Create preview URL
    const reader = new FileReader();
    reader.onloadend = () => {
      setPreviewUrl(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleRemoveFile = () => {
    setSelectedFile(null);
    setPreviewUrl(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(false);

    try {
      // Validate form
      if (!formData.email.trim()) {
        setError("Email is required");
        setSubmitting(false);
        return;
      }

      // Create FormData
      const formDataToSend = new FormData();
      formDataToSend.append("email", formData.email);
      if (formData.description.trim()) {
        formDataToSend.append("description", formData.description);
      }
      if (selectedFile) {
        formDataToSend.append("file", selectedFile);
      }

      // Submit contact form
      const response = await apiClient.submitContact(
        formData.email,
        formData.description || undefined,
        selectedFile || undefined
      );

      if (response.error) {
        setError(response.error);
      } else {
        setSuccess(true);
        // Reset form
        setFormData({ email: userEmail, description: "" });
        setSelectedFile(null);
        setPreviewUrl(null);
        // Clear success message after 5 seconds
        setTimeout(() => setSuccess(false), 5000);
      }
    } catch (err) {
      setError("Failed to submit contact form. Please try again.");
      console.error("Contact submission error:", err);
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-2xl mx-auto">
        <div className="bg-white shadow rounded-lg p-6 sm:p-8">
          <div className="mb-6">
            <h1 className="text-2xl font-bold text-gray-900">Contact Us</h1>
            <p className="mt-2 text-sm text-gray-600">
              Have a question or found an issue? Please fill out the form below
              and we'll get back to you.
            </p>
          </div>

          {error && (
            <div className="mb-6 bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          {success && (
            <div className="mb-6 bg-green-50 border border-green-200 rounded-md p-4">
              <div className="text-sm text-green-700">
                Your message has been submitted successfully! We'll get back to
                you soon.
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-6">
            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="your@email.com" 
                disabled={true}
              />
            </div>

            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700"
              >
                Description / Note
              </label>
              <textarea
                id="description"
                name="description"
                rows={6}
                value={formData.description}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Please describe your question or the issue you encountered..."
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Screenshot (Optional)
              </label>
              <p className="text-xs text-gray-500 mb-3">
                Upload a screenshot of the error (PNG, JPEG, JPG only, max 10MB)
              </p>

              {!selectedFile ? (
                <FileUpload
                  onFileSelect={handleFileSelect}
                  accept=".png,.jpeg,.jpg"
                  maxSize={10}
                />
              ) : (
                <div className="border-2 border-gray-300 rounded-lg p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-3">
                      {previewUrl && (
                        <img
                          src={previewUrl}
                          alt="Preview"
                          className="h-16 w-16 object-cover rounded"
                        />
                      )}
                      <div>
                        <p className="text-sm font-medium text-gray-900">
                          {selectedFile.name}
                        </p>
                        <p className="text-xs text-gray-500">
                          {(selectedFile.size / 1024).toFixed(2)} KB
                        </p>
                      </div>
                    </div>
                    <button
                      type="button"
                      onClick={handleRemoveFile}
                      className="text-red-600 hover:text-red-800 text-sm font-medium"
                    >
                      Remove
                    </button>
                  </div>
                </div>
              )}
            </div>

            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => router.back()}
                className="px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={submitting}
                className="px-4 py-2 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting && <LoadingSpinner size="sm" className="mr-2" />}
                Submit
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

