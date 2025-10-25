'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import apiClient from '@/utils/api-client';

interface UserProfile {
  id: string;
  username: string;
  email: string;
  created_at: string;
  preferences: {
    theme: 'light' | 'dark';
    notifications: boolean;
    language: string;
  };
}

export default function ProfilePage() {
  const router = useRouter();
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [editing, setEditing] = useState(false);
  const [formData, setFormData] = useState({
    theme: 'dark' as const,
    notifications: true,
    language: 'en',
  });
  const [saveSuccess, setSaveSuccess] = useState(false);

  useEffect(() => {
    loadProfile();
  }, []);

  const loadProfile = async () => {
    try {
      setLoading(true);
      // TODO: Replace with actual API call
      const mockProfile: UserProfile = {
        id: '1',
        username: 'cryptocoder',
        email: 'user@example.com',
        created_at: new Date().toISOString(),
        preferences: {
          theme: 'dark',
          notifications: true,
          language: 'en',
        },
      };
      setProfile(mockProfile);
      setFormData(mockProfile.preferences);
    } catch (err) {
      console.error('Failed to load profile:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePreferences = async () => {
    try {
      // TODO: Replace with actual API call
      setSaveSuccess(true);
      setEditing(false);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (err) {
      console.error('Failed to save preferences:', err);
    }
  };

  const handleLogout = () => {
    apiClient.logout();
    router.push('/auth/login');
  };

  const handleChangePassword = () => {
    // TODO: Implement password change modal
    console.log('Change password clicked');
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading profile...</p>
        </div>
      </div>
    );
  }

  if (!profile) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-gray-400">Failed to load profile</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900 text-white">
      {/* Header */}
      <div className="border-b border-gray-800 bg-gray-800/50 backdrop-blur">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <h1 className="text-3xl font-bold">Account Settings</h1>
          <p className="text-gray-400 mt-1">Manage your profile and preferences</p>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
        {/* Profile Section */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-6">Profile Information</h2>
          
          <div className="space-y-4">
            {/* Username */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Username</label>
              <p className="text-lg text-white">{profile.username}</p>
            </div>

            {/* Email */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Email</label>
              <p className="text-lg text-white">{profile.email}</p>
            </div>

            {/* Member Since */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Member Since</label>
              <p className="text-lg text-white">
                {new Date(profile.created_at).toLocaleDateString('en-US', {
                  year: 'numeric',
                  month: 'long',
                  day: 'numeric',
                })}
              </p>
            </div>
          </div>
        </div>

        {/* Preferences Section */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-semibold text-white">Preferences</h2>
            {!editing && (
              <button
                onClick={() => setEditing(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
              >
                Edit
              </button>
            )}
          </div>

          {saveSuccess && (
            <div className="mb-4 p-4 bg-green-900/50 border border-green-600 rounded-lg text-green-300">
              Preferences saved successfully!
            </div>
          )}

          <div className="space-y-6">
            {/* Theme */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Theme</label>
              {editing ? (
                <select
                  value={formData.theme}
                  onChange={(e) => setFormData({...formData, theme: e.target.value as 'light' | 'dark'})}
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="dark">Dark</option>
                  <option value="light">Light</option>
                </select>
              ) : (
                <p className="text-lg text-white capitalize">{profile.preferences.theme}</p>
              )}
            </div>

            {/* Language */}
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-2">Language</label>
              {editing ? (
                <select
                  value={formData.language}
                  onChange={(e) => setFormData({...formData, language: e.target.value})}
                  className="px-3 py-2 bg-gray-700 border border-gray-600 rounded-lg text-white focus:outline-none focus:border-blue-500"
                >
                  <option value="en">English</option>
                  <option value="es">Spanish</option>
                  <option value="fr">French</option>
                  <option value="de">German</option>
                </select>
              ) : (
                <p className="text-lg text-white">English</p>
              )}
            </div>

            {/* Notifications */}
            <div>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={formData.notifications}
                  onChange={(e) => setFormData({...formData, notifications: e.target.checked})}
                  disabled={!editing}
                  className="w-4 h-4 rounded border-gray-600 text-blue-600 focus:ring-blue-500"
                />
                <span className="ml-2 text-sm font-medium text-gray-300">Enable notifications</span>
              </label>
              <p className="text-xs text-gray-500 mt-1">Receive updates about portfolio changes and market alerts</p>
            </div>

            {/* Action Buttons */}
            {editing && (
              <div className="flex gap-3 pt-4">
                <button
                  onClick={handleSavePreferences}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors"
                >
                  Save Changes
                </button>
                <button
                  onClick={() => setEditing(false)}
                  className="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
                >
                  Cancel
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Security Section */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold text-white mb-6">Security</h2>
          
          <div className="space-y-4">
            <button
              onClick={handleChangePassword}
              className="w-full px-4 py-2 border border-gray-600 rounded-lg text-gray-300 hover:bg-gray-700 transition-colors text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold">Change Password</p>
                  <p className="text-sm text-gray-500">Update your password regularly to keep your account secure</p>
                </div>
                <span className="text-gray-400">→</span>
              </div>
            </button>

            <div className="px-4 py-3 bg-gray-700/50 border border-gray-600 rounded-lg">
              <p className="text-sm text-gray-300">
                <span className="font-semibold">Last password change:</span> Never
              </p>
            </div>
          </div>
        </div>

        {/* Danger Zone */}
        <div className="bg-red-900/30 rounded-lg p-6 border border-red-700">
          <h2 className="text-xl font-semibold text-red-400 mb-6">Danger Zone</h2>
          
          <div className="space-y-3">
            <button
              onClick={handleLogout}
              className="w-full px-4 py-2 border border-red-600 rounded-lg text-red-400 hover:bg-red-900/50 transition-colors text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold">Log Out</p>
                  <p className="text-sm text-red-300">Sign out from this device</p>
                </div>
                <span className="text-red-400">→</span>
              </div>
            </button>

            <button
              className="w-full px-4 py-2 border border-red-600 rounded-lg text-red-400 hover:bg-red-900/50 transition-colors text-left"
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-semibold">Delete Account</p>
                  <p className="text-sm text-red-300">Permanently delete your account and all data</p>
                </div>
                <span className="text-red-400">→</span>
              </div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
