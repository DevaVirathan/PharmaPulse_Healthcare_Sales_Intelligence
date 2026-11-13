import { useState, useEffect } from 'react';
import apiClient from '../services/api';

export function useMasterData() {
  const [brands, setBrands] = useState([]);
  const [regions, setRegions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let mounted = true;
    async function fetchMasterData() {
      try {
        setLoading(true);
        const [brandsRes, regionsRes] = await Promise.all([
          apiClient.getBrands(),
          apiClient.getRegions(),
        ]);
        if (mounted) {
          setBrands(brandsRes.data.items || []);
          setRegions(regionsRes.data.items || []);
          setError(null);
        }
      } catch (err) {
        if (mounted) {
          setError(err.message || 'Failed to load master data');
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }
    fetchMasterData();
    return () => {
      mounted = false;
    };
  }, []);

  return { brands, regions, loading, error };
}
