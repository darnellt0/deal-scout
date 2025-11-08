"use client";

import { useCallback, useState } from "react";
import useSWR from "swr";
import {
  DealAlertRule,
  fetchDealAlertRules,
  createDealAlertRule,
  updateDealAlertRule,
  deleteDealAlertRule,
  testDealAlertRule,
  pauseDealAlertRule,
  resumeDealAlertRule,
  Deal,
  CreateDealAlertRuleRequest,
} from "../../../lib/api";
import CreateAlertModal from "../../../components/CreateAlertModal";
import AlertRuleCard from "../../../components/AlertRuleCard";
import TestResultsModal from "../../../components/TestResultsModal";

export default function DealAlertsPage() {
  const { data: rules, isLoading, mutate } = useSWR<DealAlertRule[]>(
    "deal-alert-rules",
    fetchDealAlertRules,
    { refreshInterval: 30_000 }
  );

  const [showCreateModal, setShowCreateModal] = useState(false);
  const [testResults, setTestResults] = useState<Deal[] | null>(null);
  const [testingRuleId, setTestingRuleId] = useState<number | null>(null);
  const [status, setStatus] = useState<string>();
  const [error, setError] = useState<string>();

  const handleCreateRule = useCallback(
    async (data: CreateDealAlertRuleRequest) => {
      try {
        setStatus("Creating deal alert rule...");
        setError(undefined);
        await createDealAlertRule(data);
        await mutate();
        setStatus("Deal alert rule created successfully!");
        setShowCreateModal(false);
        setTimeout(() => setStatus(undefined), 3000);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Unknown error";
        setError(msg);
      }
    },
    [mutate]
  );

  const handleTestRule = useCallback(
    async (ruleId: number) => {
      try {
        setTestingRuleId(ruleId);
        const results = await testDealAlertRule(ruleId);
        setTestResults(results);
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to test rule";
        setError(msg);
      } finally {
        setTestingRuleId(null);
      }
    },
    []
  );

  const handleToggleRule = useCallback(
    async (rule: DealAlertRule) => {
      try {
        setError(undefined);
        if (rule.enabled) {
          await pauseDealAlertRule(rule.id);
        } else {
          await resumeDealAlertRule(rule.id);
        }
        await mutate();
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to toggle rule";
        setError(msg);
      }
    },
    [mutate]
  );

  const handleDeleteRule = useCallback(
    async (ruleId: number) => {
      if (!confirm("Are you sure you want to delete this rule?")) return;

      try {
        setError(undefined);
        await deleteDealAlertRule(ruleId);
        await mutate();
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Failed to delete rule";
        setError(msg);
      }
    },
    [mutate]
  );

  const enabledCount = rules?.filter((r) => r.enabled).length ?? 0;

  return (
    <div className="flex flex-col gap-6">
      <header className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
        <div>
          <h1 className="text-2xl font-semibold text-slate-900">
            Deal Alert Rules
          </h1>
          <p className="text-sm text-slate-500">
            Create custom rules to get notified about deals matching your criteria.
          </p>
        </div>
        <button
          onClick={() => setShowCreateModal(true)}
          className="rounded bg-brand px-4 py-2 text-sm font-medium text-white shadow hover:bg-brand-dark"
        >
          + New Alert Rule
        </button>
      </header>

      {status && (
        <div className="rounded-lg border border-green-200 bg-green-50 p-4">
          <p className="text-sm text-green-800">{status}</p>
        </div>
      )}

      {error && (
        <div className="rounded-lg border border-red-200 bg-red-50 p-4">
          <p className="text-sm text-red-800">{error}</p>
        </div>
      )}

      {isLoading ? (
        <div className="text-center py-12">
          <p className="text-slate-500">Loading deal alert rules...</p>
        </div>
      ) : !rules || rules.length === 0 ? (
        <div className="rounded-lg border border-dashed border-slate-300 p-12 text-center">
          <p className="mb-4 text-slate-600">No deal alert rules yet.</p>
          <button
            onClick={() => setShowCreateModal(true)}
            className="text-sm font-medium text-brand hover:underline"
          >
            Create your first rule
          </button>
        </div>
      ) : (
        <>
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium text-slate-600">Total Rules</p>
              <p className="mt-2 text-2xl font-bold text-slate-900">{rules.length}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium text-slate-600">Active Rules</p>
              <p className="mt-2 text-2xl font-bold text-green-600">{enabledCount}</p>
            </div>
            <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-xs font-medium text-slate-600">Paused Rules</p>
              <p className="mt-2 text-2xl font-bold text-slate-600">
                {rules.length - enabledCount}
              </p>
            </div>
          </div>

          <div className="space-y-4">
            {rules.map((rule) => (
              <AlertRuleCard
                key={rule.id}
                rule={rule}
                onTest={handleTestRule}
                onToggle={handleToggleRule}
                onDelete={handleDeleteRule}
                isTesting={testingRuleId === rule.id}
              />
            ))}
          </div>
        </>
      )}

      {showCreateModal && (
        <CreateAlertModal
          onSubmit={handleCreateRule}
          onClose={() => setShowCreateModal(false)}
        />
      )}

      {testResults && (
        <TestResultsModal
          results={testResults}
          onClose={() => setTestResults(null)}
        />
      )}
    </div>
  );
}
