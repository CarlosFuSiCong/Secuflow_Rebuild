import { useState } from "react";
import { toast } from "sonner";

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

  const handleSubmit = async (data: T) => {
    setLoading(true);

    try {
      const resp = await apiCall(data);
      if (resp?.succeed) {
        toast.success(successMessage);
        if (onSuccess) {
          onSuccess(resp.data);
        }
      } else {
        toast.error(resp?.errorMessage || errorMessage);
      }
    } catch (e: any) {
      toast.error(e?.message || errorMessage);
    } finally {
      setLoading(false);
    }
  };

  return {
    loading,
    handleSubmit,
  };
}
