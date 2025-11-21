export type PasswordCriterion = {
  label: string;
  test: (password: string) => boolean;
};

export const passwordCriteria: PasswordCriterion[] = [
  { label: "At least 8 characters", test: (password) => password.length >= 8 },
  { label: "Contains at least one letter", test: (password) => /[A-Za-z]/.test(password) },
  { label: "Contains at least one number", test: (password) => /\d/.test(password) },
  { label: "Contains at least one special character", test: (password) => /[^A-Za-z0-9]/.test(password) },
];

export const isPasswordStrong = (password: string): boolean =>
  passwordCriteria.every((criterion) => criterion.test(password));

