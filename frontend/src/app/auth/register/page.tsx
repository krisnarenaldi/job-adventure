"use client";

import { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { apiClient } from "@/lib/api";
import { LoadingSpinner } from "@/components/LoadingSpinner";
import { passwordCriteria, isPasswordStrong } from "@/lib/passwordRules";

export default function Register() {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formData, setFormData] = useState({
    email: "",
    password: "",
    confirmPassword: "",
    fullName: "",
    companyName: "",
    role: "recruiter",
  });

  // Autocomplete state
  const [companies, setCompanies] = useState<
    Array<{ id: string; name: string }>
  >([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [loadingCompanies, setLoadingCompanies] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  // Normalize company name for display (matches backend logic)
  const normalizeCompanyName = (name: string) => {
    return name.toLowerCase().trim().replace(/\s+/g, " ");
  };

  // Load companies when component mounts
  useEffect(() => {
    loadCompanies();
  }, []);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target as Node)
      ) {
        setShowDropdown(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const loadCompanies = async (search?: string) => {
    setLoadingCompanies(true);
    const response = await apiClient.getCompanies(search);
    if (response.data) {
      setCompanies(response.data);
    }
    setLoadingCompanies(false);
  };

  const handleInputChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleCompanyInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setFormData((prev) => ({ ...prev, companyName: value }));
    setShowDropdown(true);

    // Debounce search
    if (value.length >= 2) {
      loadCompanies(value);
    } else {
      loadCompanies();
    }
  };

  const handleCompanySelect = (companyName: string) => {
    setFormData((prev) => ({ ...prev, companyName }));
    setShowDropdown(false);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match");
      setLoading(false);
      return;
    }

    if (!isPasswordStrong(formData.password)) {
      setError(
        "Password must be at least 8 characters and include letters, numbers, and special characters."
      );
      setLoading(false);
      return;
    }

    const response = await apiClient.register(
      formData.email,
      formData.password,
      formData.fullName,
      formData.role,
      formData.companyName
    );

    if (response.error) {
      setError(response.error);
      setLoading(false);
    } else {
      // Auto-login after registration
      const loginResponse = await apiClient.login(
        formData.email,
        formData.password
      );
      if (loginResponse.data) {
        apiClient.setToken(loginResponse.data.access_token);
        // Dispatch custom event to notify other components (like Footer)
        if (typeof window !== "undefined") {
          window.dispatchEvent(new Event("auth-change"));
        }
        router.push("/recruiter");
      } else {
        router.push("/auth/login");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            Create your account
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Or{" "}
            <Link
              href="/auth/login"
              className="font-medium text-blue-600 hover:text-blue-500"
            >
              sign in to existing account
            </Link>
          </p>
        </div>

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-md p-4">
              <div className="text-sm text-red-700">{error}</div>
            </div>
          )}

          <div className="space-y-4">
            <div>
              <label
                htmlFor="fullName"
                className="block text-sm font-medium text-gray-700"
              >
                Full Name
              </label>
              <input
                id="fullName"
                name="fullName"
                type="text"
                autoComplete="name"
                required
                value={formData.fullName}
                onChange={handleInputChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Full name"
              />
            </div>

            <div>
              <label
                htmlFor="email"
                className="block text-sm font-medium text-gray-700"
              >
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Email address"
              />
            </div>

            <div className="relative" ref={dropdownRef}>
              <label
                htmlFor="companyName"
                className="block text-sm font-medium text-gray-700"
              >
                Company Name
              </label>
              <div className="relative">
                <input
                  id="companyName"
                  name="companyName"
                  type="text"
                  autoComplete="off"
                  required
                  value={formData.companyName}
                  onChange={handleCompanyInputChange}
                  onFocus={() => setShowDropdown(true)}
                  className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                  placeholder="Select or type company name"
                />
                {loadingCompanies && (
                  <div className="absolute right-3 top-1/2 -translate-y-1/2">
                    <LoadingSpinner size="sm" />
                  </div>
                )}
              </div>

              {/* Dropdown */}
              {showDropdown && companies.length > 0 && (
                <div className="absolute z-10 mt-1 w-full bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
                  <div className="py-1">
                    {companies
                      .filter(
                        (company) =>
                          !formData.companyName ||
                          company.name
                            .toLowerCase()
                            .includes(formData.companyName.toLowerCase())
                      )
                      .map((company) => (
                        <button
                          key={company.id}
                          type="button"
                          onClick={() => handleCompanySelect(company.name)}
                          className="w-full text-left px-4 py-2 text-sm text-gray-900 hover:bg-blue-50 hover:text-blue-900 flex items-center justify-between"
                        >
                          <span>{company.name}</span>
                          <span className="text-xs text-gray-500">
                            Existing
                          </span>
                        </button>
                      ))}
                  </div>
                </div>
              )}

              <p className="mt-1 text-xs text-gray-500">
                Select an existing company or type a new one to create it.
              </p>
              {formData.companyName && (
                <p className="mt-1 text-xs text-blue-600">
                  {companies.some(
                    (c) => c.name === normalizeCompanyName(formData.companyName)
                  )
                    ? `✓ Joining existing company: "${normalizeCompanyName(
                        formData.companyName
                      )}"`
                    : `✓ Creating new company: "${normalizeCompanyName(
                        formData.companyName
                      )}"`}
                </p>
              )}
            </div>

            <div>
              <label
                htmlFor="role"
                className="block text-sm font-medium text-gray-700"
              >
                Account Type
              </label>
              <select
                id="role"
                name="role"
                value={formData.role}
                onChange={handleInputChange}
                className="mt-1 block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
              >
                <option value="recruiter">Recruiter</option>
                <option value="hiring_manager">Hiring Manager</option>
              </select>
            </div>

            <div>
              <label
                htmlFor="password"
                className="block text-sm font-medium text-gray-700"
              >
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="new-password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Password"
              />
              <ul className="mt-2 text-xs text-gray-600 space-y-1">
                {passwordCriteria.map((criterion) => {
                  const met = criterion.test(formData.password);
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
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                name="confirmPassword"
                type="password"
                autoComplete="new-password"
                required
                value={formData.confirmPassword}
                onChange={handleInputChange}
                className="mt-1 appearance-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-md focus:outline-none focus:ring-blue-500 focus:border-blue-500 sm:text-sm"
                placeholder="Confirm password"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {loading && <LoadingSpinner size="sm" className="mr-2" />}
              Create Account
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
