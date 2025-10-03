import { useState } from "react";

interface UseProfileFormOptions<T> {
  apiCall: (data: T) => Promise<any>;
  onSuccess?: (data: any) => void;
  successMessage?: string;
  errorMessage?: string;
}

export function useProfileForm<T>({
  apiCall,
  onSuccess,
  successMessage = "Updated successfully",
  errorMessage = "Update failed",
}: UseProfileFormOptions<T>) {
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);

  const handleSubmit = async (data: T) => {
    setLoading(true);
    setError(null);
    setMessage(null);

    try {
      const resp = await apiCall(data);
      if (resp?.succeed) {
        setMessage(successMessage);
        if (onSuccess) {
          onSuccess(resp.data);
        }
      } else {
        setError(resp?.errorMessage || errorMessage);
      }
    } catch (e: any) {
      setError(e?.message || errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    error,
    message,
    handleSubmit,
  };
}