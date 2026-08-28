"use client";

import React, { useState, useEffect } from "react";
import { GlassCard } from "../../components/GlassCard";
import { PageHeader } from "../../components/PageHeader";
import { formatCurrency, formatInr } from "@/lib/format";
import { api } from "@/lib/api";
import { useNav } from "@/lib/nav-context";
import {
  Layers,
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RefreshCw,
  Key,
  Lock,
  Unlock,
  Settings,
  X,
  Play,
  Activity,
  Server,
  Coins,
  ExternalLink,
} from "lucide-react";

export default function BrokerAdaptersPage() {
  const { activeBroker, setActiveBroker, refreshTelemetry, brokerBalance } = useNav();
  const [brokers, setBrokers] = useState<any[]>([]);
  const [reconciliation, setReconciliation] = useState<any>(null);
  const [reconciling, setReconciling] = useState<boolean>(false);

  // Broker Credentials Modal State
  const [selectedBroker, setSelectedBroker] = useState<any | null>(null);
  const [apiKey, setApiKey] = useState<string>("");
  const [apiSecret, setApiSecret] = useState<string>("");
  const [accountId, setAccountId] = useState<string>("");
  const [environment, setEnvironment] = useState<string>("live");
  const [extraParam1, setExtraParam1] = useState<string>("");
  const [extraParam2, setExtraParam2] = useState<string>("");

  const [saving, setSaving] = useState<boolean>(false);
  const [testing, setTesting] = useState<boolean>(false);
  const [testStatus, setTestStatus] = useState<any | null>(null);
  const [saveSuccessMessage, setSaveSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    try {
      const bList = await api.getBrokers().catch(() => []);
      setBrokers(bList || []);
    } catch (e) {
      console.warn("Failed to load broker data:", e);
    }
  };

  useEffect(() => {
    loadData();
  }, [activeBroker]);

  const handleReconcile = async () => {
    setReconciling(true);
    try {
      const res = await api.reconcileBroker(activeBroker);
      setReconciliation(res);
    } finally {
      setReconciling(false);
    }
  };

  const openConfigModal = async (broker: any) => {
    setSelectedBroker(broker);
    setTestStatus(null);
    setSaveSuccessMessage(null);

    try {
      const creds = await api.getBrokerCredentials(broker.broker_id);
      setEnvironment(creds.environment || (broker.broker_id === "BINANCE" ? "live" : "practice"));
      setApiKey("");
      setApiSecret("");
      setAccountId("");

      if (broker.broker_id === "DERIV") {
        setExtraParam1(creds.extra_params?.app_id || "1089");
      } else if (broker.broker_id === "MT5") {
        setExtraParam1(creds.extra_params?.host || "127.0.0.1");
        setExtraParam2(creds.extra_params?.port || "18812");
      }
    } catch (e) {
      console.error(e);
    }
  };

  const handleTestConnection = async () => {
    if (!selectedBroker) return;
    setTesting(true);
    setTestStatus(null);
    try {
      const res = await api.testBrokerConnection(selectedBroker.broker_id);
      setTestStatus(res);
    } catch (e: any) {
      setTestStatus({ is_connected: false, error: e.message || "Connection test failed." });
    } finally {
      setTesting(false);
    }
  };

  const handleSaveCredentials = async () => {
    if (!selectedBroker) return;
    setSaving(true);
    setSaveSuccessMessage(null);
    try {
      const extra: any = {};
      if (selectedBroker.broker_id === "DERIV" && extraParam1) {
        extra.app_id = extraParam1;
      } else if (selectedBroker.broker_id === "MT5") {
        if (extraParam1) extra.host = extraParam1;
        if (extraParam2) extra.port = parseInt(extraParam2);
      }

      await api.saveBrokerCredentials(selectedBroker.broker_id, {
        api_key: apiKey || undefined,
        api_secret: apiSecret || undefined,
        account_id: accountId || undefined,
        environment: environment,
        extra_params: Object.keys(extra).length > 0 ? extra : undefined,
      });

      setSaveSuccessMessage("Credentials encrypted with AES-256 and persisted to database & .env!");
      await loadData();
      await refreshTelemetry();
    } catch (e: any) {
      alert("Error saving credentials: " + e.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Broker Execution Adapters & Persistent Credentials"
        subtitle="Configure and test live API credentials across institutional brokers. All keys are encrypted with AES-256 and preserved across restarts."
        actions={
          <button
            onClick={handleReconcile}
            disabled={reconciling}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-lg bg-surface-elevated border border-primary-subtle hover:border-accent text-xs font-semibold text-primary transition-all shadow-sm"
          >
            <RefreshCw className={`w-3.5 h-3.5 ${reconciling ? "animate-spin text-accent" : ""}`} />
            <span>Audit Remote Reconciliation</span>
          </button>
        }
      />

      {/* Reconciliation Banner */}
      {reconciliation && (
        <GlassCard className={`p-4 border ${reconciliation.is_synced ? "bg-profit-subtle border-profit-border" : "bg-warning-subtle border-amber-500/40"}`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              {reconciliation.is_synced ? (
                <CheckCircle2 className="w-5 h-5 text-profit" />
              ) : (
                <AlertTriangle className="w-5 h-5 text-warning" />
              )}
              <div>
                <h3 className="font-bold text-sm text-primary font-mono">
                  {reconciliation.is_synced ? "Remote State Synchronized" : "Discrepancy Detected During Audit"}
                </h3>
                <p className="text-xs text-primary-muted font-mono">
                  {reconciliation.remote_positions_count} remote positions vs {reconciliation.local_positions_count} local database records
                </p>
              </div>
            </div>

            <div className="text-right font-mono text-xs">
              <span className="text-primary-muted block text-[10px]">Broker Equity</span>
              <strong className="text-primary text-sm">
                {formatCurrency(reconciliation.broker_equity)} ({formatInr(reconciliation.broker_equity)})
              </strong>
            </div>
          </div>
        </GlassCard>
      )}

      {/* Available Broker Adapters Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {brokers.map((broker) => {
          const isActive = broker.broker_id === activeBroker;
          return (
            <GlassCard key={broker.broker_id} className={`space-y-4 ${isActive ? "ring-2 ring-accent shadow-glow" : ""}`}>
              <div className="flex items-start justify-between border-b border-primary-subtle pb-3">
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="font-bold text-base text-primary">{broker.name}</h3>
                    {isActive && (
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold font-mono bg-accent text-background">
                        ACTIVE
                      </span>
                    )}
                  </div>
                  <span className="text-xs font-mono text-primary-muted">{broker.broker_id}</span>
                </div>

                <span className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                  broker.is_connected ? "bg-profit-subtle text-profit border border-profit-border" : "bg-surface-elevated text-primary-muted border border-primary-subtle"
                }`}>
                  {broker.is_connected ? "CONNECTED" : "UNCONFIGURED"}
                </span>
              </div>

              {/* Specs */}
              <div className="space-y-2 text-xs font-mono">
                <div className="flex justify-between">
                  <span className="text-primary-muted">Environment:</span>
                  <strong className="text-primary uppercase">{broker.environment}</strong>
                </div>
                <div className="flex justify-between">
                  <span className="text-primary-muted">Latency:</span>
                  <strong className="text-primary">{broker.latency_ms?.toFixed(1)}ms</strong>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-primary-muted">Stored Key:</span>
                  <strong className="text-accent bg-accent/10 px-2 py-0.5 rounded border border-accent/20 truncate max-w-[140px]">
                    {broker.api_key_masked || "None"}
                  </strong>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="grid grid-cols-2 gap-2 pt-2 border-t border-primary-subtle">
                <button
                  onClick={() => openConfigModal(broker)}
                  className="py-2 px-3 rounded-lg bg-surface-elevated border border-primary-subtle hover:border-accent text-xs font-bold text-primary flex items-center justify-center gap-1.5 transition-all shadow-sm font-mono"
                >
                  <Key className="w-3.5 h-3.5 text-accent" />
                  <span>Configure Keys</span>
                </button>

                {!isActive ? (
                  <button
                    onClick={() => setActiveBroker(broker.broker_id)}
                    className="py-2 px-3 rounded-lg bg-accent text-background hover:bg-accent-hover text-xs font-bold transition-all shadow-sm font-mono"
                  >
                    Set Active
                  </button>
                ) : (
                  <div className="py-2 text-center text-xs font-bold text-profit font-mono bg-profit-subtle border border-profit-border rounded-lg">
                    ACTIVE ROUTE
                  </div>
                )}
              </div>
            </GlassCard>
          );
        })}
      </div>

      {/* Broker Credentials & Configuration Modal */}
      {selectedBroker && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4">
          <div className="bg-surface rounded-2xl border border-primary-subtle shadow-elevation max-w-xl w-full p-6 space-y-4 animate-in fade-in zoom-in-95 duration-150 max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="flex items-center justify-between border-b border-primary-subtle pb-3">
              <div className="flex items-center gap-2.5">
                <Key className="w-5 h-5 text-accent" />
                <div>
                  <h3 className="text-base font-bold text-primary">Configure {selectedBroker.name}</h3>
                  <p className="text-xs text-primary-muted font-mono">{selectedBroker.broker_id}</p>
                </div>
              </div>
              <button
                onClick={() => setSelectedBroker(null)}
                className="p-1 rounded-lg text-primary-muted hover:text-primary hover:bg-surface-elevated"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            {/* Persistent Security Info */}
            <div className="p-3 rounded-xl bg-profit-subtle border border-profit-border flex items-start gap-2.5 text-xs text-primary">
              <ShieldCheck className="w-4 h-4 text-profit flex-shrink-0 mt-0.5" />
              <span>
                Credentials are encrypted with <strong>AES-256 Fernet</strong> and saved in persistent local storage. They remain active even after platform restart or refresh.
              </span>
            </div>

            {/* Binance API Setup Guide (if Binance selected) */}
            {selectedBroker.broker_id === "BINANCE" && (
              <div className="p-3.5 rounded-xl bg-surface-elevated border border-accent/30 text-xs font-mono space-y-1.5 text-primary">
                <div className="flex items-center gap-1.5 font-bold text-accent">
                  <ExternalLink className="w-3.5 h-3.5" />
                  <span>Binance API Requirements for Live Balance (₹ / $)</span>
                </div>
                <ul className="list-disc pl-4 space-y-1 text-primary-muted text-[11px]">
                  <li>In Binance <strong>API Management</strong>, ensure <strong className="text-primary">"Enable Reading"</strong> is checked.</li>
                  <li>Under <strong>IP Access Restrictions</strong>, choose <strong className="text-primary">"Unrestricted"</strong> (or add your current public IP).</li>
                  <li>Use Spot Account API Keys (not Futures-only sub-keys).</li>
                </ul>
              </div>
            )}

            {/* Form Fields tailored to Broker */}
            <div className="space-y-3 font-mono text-xs">
              {/* Environment Toggle */}
              <div>
                <label className="text-primary-muted font-bold block mb-1">Execution Environment</label>
                <select
                  value={environment}
                  onChange={(e) => setEnvironment(e.target.value)}
                  className="w-full p-2.5 rounded-lg bg-surface-elevated border border-primary-subtle font-bold text-primary"
                >
                  {selectedBroker.broker_id === "BINANCE" && (
                    <>
                      <option value="live">Binance Live Spot (api.binance.com)</option>
                      <option value="testnet">Binance Spot Testnet (testnet.binance.vision)</option>
                    </>
                  )}
                  {selectedBroker.broker_id === "OANDA" && (
                    <>
                      <option value="practice">OANDA fxPractice (api-fxpractice.oanda.com)</option>
                      <option value="trade">OANDA Live (api-fxtrade.oanda.com)</option>
                    </>
                  )}
                  {selectedBroker.broker_id === "DERIV" && (
                    <option value="deriv_ws">Deriv WebSocket Engine</option>
                  )}
                  {selectedBroker.broker_id === "MT5" && (
                    <option value="mt5_terminal">MetaTrader 5 Client Bridge</option>
                  )}
                  {selectedBroker.broker_id === "MOCK_BROKER" && (
                    <option value="paper">Simulated Paper Engine</option>
                  )}
                  {selectedBroker.broker_id === "CUSTOM_REST" && (
                    <option value="custom">Custom Webhook / REST</option>
                  )}
                </select>
              </div>

              {/* API Key / Token Field */}
              {selectedBroker.broker_id !== "MT5" && selectedBroker.broker_id !== "MOCK_BROKER" && (
                <div>
                  <label className="text-primary-muted font-bold block mb-1">
                    {selectedBroker.broker_id === "DERIV" ? "API Token" : "API Key"}
                  </label>
                  <input
                    type="password"
                    placeholder="Enter API Key / Token"
                    value={apiKey}
                    onChange={(e) => setApiKey(e.target.value)}
                    className="w-full p-2.5 rounded-lg bg-surface-elevated border border-primary-subtle font-mono text-primary font-medium focus:border-accent"
                  />
                </div>
              )}

              {/* API Secret (Binance) */}
              {selectedBroker.broker_id === "BINANCE" && (
                <div>
                  <label className="text-primary-muted font-bold block mb-1">API Secret (HMAC-SHA256)</label>
                  <input
                    type="password"
                    placeholder="Enter API Secret"
                    value={apiSecret}
                    onChange={(e) => setApiSecret(e.target.value)}
                    className="w-full p-2.5 rounded-lg bg-surface-elevated border border-primary-subtle font-mono text-primary font-medium focus:border-accent"
                  />
                </div>
              )}

              {/* Account ID (OANDA) */}
              {selectedBroker.broker_id === "OANDA" && (
                <div>
                  <label className="text-primary-muted font-bold block mb-1">OANDA Account ID (e.g. 101-001-XXXX-001)</label>
                  <input
                    type="text"
                    placeholder="Enter Account ID"
                    value={accountId}
                    onChange={(e) => setAccountId(e.target.value)}
                    className="w-full p-2.5 rounded-lg bg-surface-elevated border border-primary-subtle font-mono text-primary font-medium focus:border-accent"
                  />
                </div>
              )}

              {/* Deriv App ID */}
              {selectedBroker.broker_id === "DERIV" && (
                <div>
                  <label className="text-primary-muted font-bold block mb-1">Deriv App ID</label>
                  <input
                    type="text"
                    placeholder="1089"
                    value={extraParam1}
                    onChange={(e) => setExtraParam1(e.target.value)}
                    className="w-full p-2.5 rounded-lg bg-surface-elevated border border-primary-subtle font-mono text-primary font-medium"
                  />
                </div>
              )}

              {/* MT5 Host & Port */}
              {selectedBroker.broker_id === "MT5" && (
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <label className="text-primary-muted font-bold block mb-1">Bridge Host</label>
                    <input
                      type="text"
                      placeholder="127.0.0.1"
                      value={extraParam1 || "127.0.0.1"}
                      onChange={(e) => setExtraParam1(e.target.value)}
                      className="w-full p-2.5 rounded-lg bg-surface-elevated border border-primary-subtle font-mono text-primary font-medium"
                    />
                  </div>
                  <div>
                    <label className="text-primary-muted font-bold block mb-1">Bridge Port</label>
                    <input
                      type="number"
                      placeholder="18812"
                      value={extraParam2 || "18812"}
                      onChange={(e) => setExtraParam2(e.target.value)}
                      className="w-full p-2.5 rounded-lg bg-surface-elevated border border-primary-subtle font-mono text-primary font-medium"
                    />
                  </div>
                </div>
              )}
            </div>

            {/* Test Connection Output */}
            {testStatus && (
              <div className={`p-3 rounded-xl border text-xs font-mono ${
                testStatus.is_connected ? "bg-profit-subtle border-profit-border text-profit" : "bg-loss-subtle border-loss-border text-loss"
              }`}>
                <div className="flex items-center justify-between">
                  <span className="font-bold">
                    {testStatus.is_connected ? "Connection Successful!" : "Connection Failed"}
                  </span>
                  {testStatus.latency_ms > 0 && <span>Latency: {testStatus.latency_ms}ms</span>}
                </div>
                {testStatus.error && <p className="mt-1 text-[11px] opacity-90">{testStatus.error}</p>}
                {testStatus.balance && (
                  <p className="mt-1 text-[11px]">
                    Available Equity: {formatCurrency(testStatus.balance.equity, testStatus.balance.currency || "USD")} ({formatInr(testStatus.balance.equity)})
                  </p>
                )}
              </div>
            )}

            {/* Success Banner */}
            {saveSuccessMessage && (
              <div className="p-3 rounded-xl bg-profit-subtle border border-profit-border text-profit text-xs font-mono font-bold flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
                <span>{saveSuccessMessage}</span>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex items-center gap-3 pt-3 border-t border-primary-subtle">
              <button
                type="button"
                onClick={handleTestConnection}
                disabled={testing}
                className="flex-1 py-2.5 rounded-xl bg-surface-elevated border border-primary-subtle hover:border-accent text-primary font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-sm font-mono"
              >
                <Activity className={`w-3.5 h-3.5 ${testing ? "animate-spin text-accent" : ""}`} />
                <span>{testing ? "Testing..." : "Test Connection"}</span>
              </button>

              <button
                type="button"
                onClick={handleSaveCredentials}
                disabled={saving}
                className="flex-1 py-2.5 rounded-xl bg-accent text-background hover:bg-accent-hover font-bold text-xs flex items-center justify-center gap-1.5 transition-all shadow-sm font-mono"
              >
                <Lock className="w-3.5 h-3.5" />
                <span>{saving ? "Encrypting..." : "Save & Encrypt (AES-256)"}</span>
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
