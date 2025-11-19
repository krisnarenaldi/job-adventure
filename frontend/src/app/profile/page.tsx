"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiClient } from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { passwordCriteria, isPasswordStrong } from "@/lib/passwordRules";

export default function ProfilePage() {
  const router = useRouter();
  const [initializing, setInitializing] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [userEmail, setUserEmail] = useState<string>("");
  const [formData, setFormData] = useState({
    currentPassword: "",
    newPassword: "",
    confirmPassword: "",
  });

  useEffect(() => {
    const token = localStorage.getItem("auth_token");
    if (!token) {
      router.push("/auth/login");
      return;
    }

    const fetchUser = async () => {
      const response = await apiClient.getCurrentUser();
      if (response.data) {
        setUserEmail(response.data.email);
        setInitializing(false);
      } else {
        router.push("/auth/login");
      }
    };

    fetchUser();
  }, [router]);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    setSuccess(null);

    if (formData.newPassword !== formData.confirmPassword) {
      setError("New passwords do not match.");
      setSubmitting(false);
      return;
    }

    if (!isPasswordStrong(formData.newPassword)) {
      setError(
        "New password must be at least 8 characters and include letters, numbers, and special characters."
      );
      setSubmitting(false);
      return;
    }

    const response = await apiClient.changePassword(
      formData.currentPassword,
      formData.newPassword
    );

    if (response.error) {
      setError(response.error);
    } else {
      setSuccess("Password updated successfully.");
      setFormData({
        currentPassword: "",
        newPassword: "",
        confirmPassword: "",
      });
    }
    setSubmitting(false);
  };

  if (initializing) {
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
            <h1 className="text-2xl font-bold text-gray-900">Profile</h1>
            <p className="text-sm text-gray-600 mt-1">
              Signed in as <span className="font-medium">{userEmail}</span>
            </p>
            <p className="text-sm text-gray-500 mt-2">
              You can only update your password from this page. Email and company
              details are managed by administrators.
            </p>
          </div>

          {error && (
            <div className="mb-4 bg-red-50 border border-red-200 rounded-md p-4 text-sm text-red-700">
              {error}
            </div>
          )}

          {success && (
            <div className="mb-4 bg-green-50 border border-green-200 rounded-md p-4 text-sm text-green-700">
              {success}
            </div>
          )}

          <form className="space-y-6" onSubmit={handleSubmit}>
            <div>
              <label
                htmlFor="currentPassword"
                className="block text-sm font-medium text-gray-700"
              >
                Current Password
              </label>
              <input
                id="currentPassword"
                name="currentPassword"
                type="password"
                required
                value={formData.currentPassword}
                onChange={handleInputChange}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                placeholder="Enter current password"
              />
            </div>

            <div>
              <label
                htmlFor="newPassword"
                className="block text-sm font-medium text-gray-700"
              >
                New Password
              </label>
              <input
                id="newPassword"
                name="newPassword"
                type="password"
                required
                value={formData.newPassword}
                onChange={handleInputChange}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                placeholder="Enter new password"
              />
              <ul className="mt-2 text-xs text-gray-600 space-y-1">
                {passwordCriteria.map((criterion) => {
                  const met = criterion.test(formData.newPassword);
                  return (
                    <li
                      key={criterion.label}
                      className={met ? "text-green-600" : "text-gray-500"}
                    >
                      {met ? "✓" : "•"} {criterion.label}
                    </li>
                  );
                })}
              </ul>
            </div>

            <div>
              <label
                htmlFor="confirmPassword"
                className="block text-sm font-medium text-gray-700"
              >
                Confirm New Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                required
                value={formData.confirmPassword}
                onChange={handleInputChange}
                className="mt-1 block w-full rounded-md border border-gray-300 px-3 py-2 shadow-sm focus:border-blue-500 focus:outline-none focus:ring-blue-500 sm:text-sm"
                placeholder="Confirm new password"
              />
            </div>

            <div>
              <button
                type="submit"
                disabled={submitting}
                className="inline-flex items-center justify-center w-full rounded-md border border-transparent bg-blue-600 px-4 py-2 text-sm font-medium text-white shadow-sm hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {submitting && <LoadingSpinner size="sm" className="mr-2" />}
                Update Password
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

