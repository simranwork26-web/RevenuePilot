"use client";

import dynamic from "next/dynamic";
import { useEffect, useState } from "react";
import {
  Activity,
  ArrowDownRight,
  Bell,
  ChevronDown,
  CircleHelp,
  CreditCard,
  Download,
  LayoutDashboard,
  MapPinned,
  Menu,
  Package,
  Search,
  Settings2,
  ShoppingCart,
  Sparkles,
  Users,
  X,
} from "lucide-react";
import {
  getDashboardKpis,
  getMonthlyRevenue,
  getCategories,
  getRegions,
  getCustomerSegments,
  getCustomerRetention,
  getRevenueForecast,
  type RevenueForecast,
  type CustomerRetention,
  type DashboardKpis,
  type MonthlyRevenue,
  type CategoryMetric,
  type RegionMetric,
  type CustomerSegment,
} from "@/lib/api";

const RevenueChart = dynamic(() => import("echarts-for-react"), {
  ssr: false,
  loading: () => <div className="chart-loading">Preparing revenue chart…</div>,
});

const navigation = [
  { label: "Overview", icon: LayoutDashboard },
  { label: "Revenue analysis", icon: CreditCard },
  { label: "Products & categories", icon: Package },
  { label: "Regional performance", icon: MapPinned },
  { label: "Customer intelligence", icon: Users },
];

const themes = [
  { id: "executive", label: "Executive Light", color: "#2563eb" },
  { id: "midnight", label: "Midnight Indigo", color: "#818cf8" },
  { id: "warm", label: "Warm Neutral", color: "#71816a" },
];

const buildRevenueOption = (monthlyData: MonthlyRevenue[]) => ({
  animationDuration: 650,
  tooltip: {
    trigger: "axis",
    backgroundColor: "#142d4e",
    borderWidth: 0,
    textStyle: { color: "#ffffff" },
    formatter: (params: { axisValue: string; value: number }[]) =>
      `${params[0].axisValue}<br/><strong>${formatMoney(params[0].value)}</strong>`,
  },
  grid: { left: 8, right: 12, top: 20, bottom: 8, containLabel: true },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: monthlyData.map((row) => {
      const [year, month] = row.month.split("-").map(Number);
      return new Date(year, month - 1, 1).toLocaleDateString("en-US", {
        month: "short",
        year: "2-digit",
      });
    }),
    axisLine: { lineStyle: { color: "#e5eaf1" } },
    axisTick: { show: false },
    axisLabel: { color: "#8390a5", fontSize: 11, margin: 14 },
  },
  yAxis: {
    type: "value",
    splitNumber: 4,
    axisLabel: {
      color: "#8390a5",
      fontSize: 11,
      formatter: (value: number) =>
        value === 0 ? "0" : `${(value / 1000000).toFixed(1)}M`,
    },
    splitLine: { lineStyle: { color: "#edf1f6", type: "dashed" } },
  },
  series: [
    {
      name: "Delivered item value",
      type: "line",
      smooth: 0.35,
      symbol: "circle",
      symbolSize: 5,
      data: monthlyData.map((row) => row.delivered_item_value),
      lineStyle: { color: "#2563eb", width: 3 },
      itemStyle: { color: "#2563eb", borderColor: "#ffffff", borderWidth: 2 },
      areaStyle: {
        color: {
          type: "linear",
          x: 0,
          y: 0,
          x2: 0,
          y2: 1,
          colorStops: [
            { offset: 0, color: "rgba(37,99,235,0.18)" },
            { offset: 1, color: "rgba(37,99,235,0.01)" },
          ],
        },
      },
    },
  ],
});

const buildForecastOption = (
  forecast: RevenueForecast["forecast"],
) => ({
  animationDuration: 650,
  tooltip: {
    trigger: "axis",
    backgroundColor: "#142d4e",
    borderWidth: 0,
    textStyle: { color: "#ffffff" },
    formatter: (params: { axisValue: string; value: number }[]) =>
      `${params[0].axisValue}<br/><strong>${formatMoney(params[0].value)}</strong>`,
  },
  grid: { left: 8, right: 16, top: 20, bottom: 8, containLabel: true },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: forecast.map((row) =>
      new Date(`${row.week_start.slice(0, 10)}T12:00:00`).toLocaleDateString(
        "en-US",
        { month: "short", day: "numeric", year: "2-digit" },
      ),
    ),
    axisLine: { lineStyle: { color: "#e5eaf1" } },
    axisTick: { show: false },
    axisLabel: { color: "#8390a5", fontSize: 10, margin: 12 },
  },
  yAxis: {
    type: "value",
    min: 0,
    splitNumber: 4,
    axisLabel: {
      color: "#8390a5",
      fontSize: 10,
      formatter: (value: number) => `${Math.round(value / 1000)}k`,
    },
    splitLine: { lineStyle: { color: "#edf1f6", type: "dashed" } },
  },
  series: [
    {
      name: "Historical trend projection",
      type: "line",
      smooth: 0.25,
      symbol: "circle",
      symbolSize: 8,
      data: forecast.map((row) => row.forecast_revenue),
      lineStyle: { color: "#7c5ce0", width: 3, type: "dashed" },
      itemStyle: { color: "#7c5ce0", borderColor: "#ffffff", borderWidth: 2 },
      areaStyle: { color: "rgba(124,92,224,0.10)" },
    },
  ],
});

const categoryColors = [
  "#2563eb",
  "#6092ed",
  "#8bb0f5",
  "#b3caf7",
  "#d1def8",
];

const categoryLabels: Record<string, string> = {
  health_beauty: "Health & beauty",
  watches_gifts: "Watches & gifts",
  bed_bath_table: "Bed & bath table",
  sports_leisure: "Sports & leisure",
  computers_accessories: "Computers & accessories",
};

const stateLabels: Record<string, string> = {
  SP: "São Paulo",
  RJ: "Rio de Janeiro",
  MG: "Minas Gerais",
  RS: "Rio Grande do Sul",
  PR: "Paraná",
  SC: "Santa Catarina",
  BA: "Bahia",
  DF: "Distrito Federal",
  GO: "Goiás",
  ES: "Espírito Santo",
  PE: "Pernambuco",
  CE: "Ceará",
  PA: "Pará",
  MT: "Mato Grosso",
  MA: "Maranhão",
  MS: "Mato Grosso do Sul",
  PB: "Paraíba",
  PI: "Piauí",
  RN: "Rio Grande do Norte",
  AL: "Alagoas",
  SE: "Sergipe",
  TO: "Tocantins",
  RO: "Rondônia",
  AM: "Amazonas",
  AC: "Acre",
  AP: "Amapá",
  RR: "Roraima",
};

const formatMoney = (value: number) =>
  new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
    maximumFractionDigits: 0,
  }).format(value);

export default function Home() {
  const [theme, setTheme] = useState("executive");
  const [activePage, setActivePage] = useState("Overview");
  const [showThemes, setShowThemes] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);
  const [kpis, setKpis] = useState<DashboardKpis | null>(null);
  const [monthlyRevenue, setMonthlyRevenue] = useState<MonthlyRevenue[]>([]);
  const [monthlyError, setMonthlyError] = useState<string | null>(null);
  const [categories, setCategories] = useState<CategoryMetric[]>([]);
  const [regions, setRegions] = useState<RegionMetric[]>([]);
  const [categoryError, setCategoryError] = useState<string | null>(null);
  const [regionError, setRegionError] = useState<string | null>(null);
  const [customerSegments, setCustomerSegments] = useState<CustomerSegment[]>([]);
  const [segmentError, setSegmentError] = useState<string | null>(null);
  const [customerRetention, setCustomerRetention] = useState<CustomerRetention | null>(null);
  const [retentionError, setRetentionError] = useState<string | null>(null);
  const [revenueForecast, setRevenueForecast] = useState<RevenueForecast | null>(null);
  const [forecastError, setForecastError] = useState<string | null>(null);
  const [kpiError, setKpiError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    getDashboardKpis()
      .then((data) => {
        if (!cancelled) setKpis(data);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setKpiError(
            error instanceof Error
              ? error.message
              : "Unable to load dashboard KPIs.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    getMonthlyRevenue()
      .then((data) => {
        if (!cancelled) setMonthlyRevenue(data);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setMonthlyError(
            error instanceof Error
              ? error.message
              : "Unable to load monthly revenue.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    getCustomerSegments()
      .then((data) => {
        if (!cancelled) setCustomerSegments(data);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setSegmentError(
            error instanceof Error
              ? error.message
              : "Unable to load customer segments.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    getCustomerRetention()
      .then((data) => {
        if (!cancelled) setCustomerRetention(data);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setRetentionError(
            error instanceof Error
              ? error.message
              : "Unable to load customer retention.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    getCategories()
      .then((data) => {
        if (!cancelled) setCategories(data);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setCategoryError(
            error instanceof Error ? error.message : "Unable to load categories.",
          );
        }
      });

    getRegions()
      .then((data) => {
        if (!cancelled) setRegions(data);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setRegionError(
            error instanceof Error ? error.message : "Unable to load regions.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;

    getRevenueForecast()
      .then((data) => {
        if (!cancelled) setRevenueForecast(data);
      })
      .catch((error: unknown) => {
        if (!cancelled) {
          setForecastError(
            error instanceof Error
              ? error.message
              : "Unable to load revenue forecast.",
          );
        }
      });

    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="app-shell" data-theme={theme}>
      <aside className={`sidebar ${mobileMenu ? "sidebar-open" : ""}`}>
        <div className="brand">
          <div className="brand-mark"><Activity size={23} strokeWidth={2.5} /></div>
          <div>
            <div className="brand-name">RevenuePilot</div>
            <div className="brand-subtitle">DECISION INTELLIGENCE</div>
          </div>
          <button className="mobile-close icon-button" onClick={() => setMobileMenu(false)} aria-label="Close menu">
            <X size={19} />
          </button>
        </div>

        <div className="workspace-label">WORKSPACE</div>
        <button className="workspace-picker">
          <span className="workspace-avatar">O</span>
          <span className="workspace-copy"><strong>Olist Commerce</strong><small>Analytics workspace</small></span>
          <ChevronDown size={16} />
        </button>

        <div className="nav-label">ANALYTICS</div>
        <nav className="nav-list" aria-label="Main navigation">
          {navigation.map(({ label, icon: Icon }) => (
            <button
              key={label}
              className={`nav-item ${activePage === label ? "nav-active" : ""}`}
              onClick={() => { setActivePage(label); setMobileMenu(false); }}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
              {label === "Customer intelligence" && <span className="nav-dot" />}
            </button>
          ))}
        </nav>

        <div className="nav-label tools-label">TOOLS</div>
        <button className="nav-item" onClick={() => setActivePage("Insights")}>
          <Sparkles size={18} strokeWidth={1.8} /><span>Business insights</span>
        </button>
        <button className="nav-item" onClick={() => setActivePage("Settings")}>
          <Settings2 size={18} strokeWidth={1.8} /><span>Settings</span>
        </button>

        <div className="sidebar-bottom">
          <div className="help-card">
            <div className="help-icon"><CircleHelp size={18} /></div>
            <strong>Need a hand?</strong>
            <p>Your business intelligence, all in one place.</p>
            <button onClick={() => setActivePage("Help")}>Explore the workspace <span>↗</span></button>
          </div>
          <div className="profile">
            <div className="profile-avatar">RP</div>
            <div className="profile-copy"><strong>RevenuePilot</strong><small>Analyst workspace</small></div>
            <button className="icon-button" aria-label="Profile options"><ChevronDown size={16} /></button>
          </div>
        </div>
      </aside>

      {mobileMenu && <button className="mobile-overlay" onClick={() => setMobileMenu(false)} aria-label="Close navigation" />}

      <section className="main-panel">
        <header className="topbar">
          <div className="topbar-left">
            <button className="mobile-menu icon-button" onClick={() => setMobileMenu(true)} aria-label="Open navigation"><Menu size={21} /></button>
            <div className="breadcrumb">Workspace <span>/</span> <strong>{activePage}</strong></div>
          </div>
          <div className="topbar-actions">
            <label className="search-box">
              <Search size={16} />
              <input aria-label="Search dashboard" placeholder="Search anything..." />
              <kbd>⌘ K</kbd>
            </label>
            <button className="icon-button notification-button" aria-label="Notifications"><Bell size={18} /><i /></button>
            <div className="topbar-divider" />
            <div className="today-label"><span>DATA PERIOD</span><strong>Historical dataset</strong></div>
          </div>
        </header>

        <div className="page-content">
          <div className="page-heading">
            <div>
              <div className="eyebrow"><span className="status-pulse" /> BUSINESS OVERVIEW</div>
              <h1>{activePage === "Overview" ? "Good morning, analyst." : activePage}</h1>
              <p className="page-description">
                {activePage === "Overview"
                  ? "Here’s what’s happening across your business."
                  : `Explore ${activePage.toLowerCase()} and uncover actionable business signals.`}
              </p>
            </div>
            <div className="heading-actions">
              <div className="theme-control">
                <button className="theme-trigger" onClick={() => setShowThemes(!showThemes)} aria-expanded={showThemes}>
                  <span className="theme-swatch" style={{ background: themes.find((item) => item.id === theme)?.color }} />
                  Theme <ChevronDown size={15} />
                </button>
                {showThemes && (
                  <div className="theme-menu">
                    <div className="theme-menu-title">APPEARANCE</div>
                    {themes.map((item) => (
                      <button key={item.id} className={`theme-option ${theme === item.id ? "theme-option-active" : ""}`} onClick={() => { setTheme(item.id); setShowThemes(false); }}>
                        <span className="theme-swatch" style={{ background: item.color }} />
                        <span>{item.label}</span>
                        {theme === item.id && <span className="theme-check">✓</span>}
                      </button>
                    ))}
                  </div>
                )}
              </div>
              <button className="export-button" onClick={() => window.print()}><Download size={16} /> Export view</button>
            </div>
          </div>

          <div className="data-notice">
            <span className="notice-icon"><Activity size={17} /></span>
            <div><strong>Olist historical data</strong><span>Dashboard metrics, revenue trends, categories, regions, and customer segments are loaded from PostgreSQL.</span></div>
            <span className="notice-tag">CONNECTED</span>
          </div>

          {kpiError && (
            <p role="alert" style={{ color: "#b91c1c", fontSize: 13 }}>
              Could not load live KPI data: {kpiError}
            </p>
          )}

          <div className="section-heading">
            <div><h2>Performance snapshot</h2><p>Your key business indicators at a glance</p></div>
            <span className="period-pill"><span /> Historical period</span>
          </div>

          <div className="kpi-grid">
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Delivered item value</span><span className="kpi-icon blue"><CreditCard size={18} /></span></div>
              <div className="kpi-value">{kpis ? formatMoney(kpis.delivered_item_value) : "Loading…"}</div>
              <div className="kpi-foot"><span className="kpi-neutral">Historical total</span><span className="kpi-caption">Delivered orders only</span></div>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Delivered orders</span><span className="kpi-icon violet"><ShoppingCart size={18} /></span></div>
              <div className="kpi-value">{kpis ? kpis.delivered_orders.toLocaleString("en-US") : "Loading…"}</div>
              <div className="kpi-foot"><span className="kpi-neutral">Historical total</span><span className="kpi-caption">Of {kpis ? kpis.total_orders.toLocaleString("en-US") : "—"} orders</span></div>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Unique customers</span><span className="kpi-icon teal"><Users size={18} /></span></div>
              <div className="kpi-value">{kpis ? kpis.unique_customers.toLocaleString("en-US") : "Loading…"}</div>
              <div className="kpi-foot"><span className="kpi-neutral">Historical total</span><span className="kpi-caption">Distinct customer IDs</span></div>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Repeat customer rate</span><span className="kpi-icon amber"><Activity size={18} /></span></div>
              <div className="kpi-value">{kpis ? kpis.repeat_customer_rate.toFixed(2) : "Loading…"}<span className="value-unit">%</span></div>
              <div className="kpi-foot"><span className="kpi-insight"><ArrowDownRight size={14} /> Retention opportunity</span><span className="kpi-caption">{kpis ? kpis.repeat_customers.toLocaleString("en-US") : "—"} repeat customers</span></div>
            </article>
          </div>

          <div className="charts-grid">
            <article className="panel revenue-panel">
              <div className="panel-header">
                <div><h3>Revenue performance</h3><p>Monthly item value trend</p></div>
                <button className="select-button">Monthly <ChevronDown size={14} /></button>
              </div>
              <div className="chart-legend"><span /><span>Delivered item value</span><small>Historical monthly data · {monthlyRevenue.length} months</small></div>
              <RevenueChart option={buildRevenueOption(monthlyRevenue)} style={{ height: 275, width: "100%" }} notMerge lazyUpdate />
              <div className="chart-footer"><span><i /> {monthlyError ? "Monthly data unavailable" : "Olist historical data"}</span><span>Values shown in BRL</span></div>
            </article>

            <article className="panel category-panel">
              <div className="panel-header"><div><h3>Top product categories</h3><p>By delivered item value</p></div><button className="more-button" aria-label="More category options">···</button></div>
              <div className="category-total">{categories.length ? formatMoney(categories[0].delivered_item_value) : "Loading…"}<span>Top category</span></div>
              <div className="category-list">
                {categoryError ? (
                  <p role="alert">{categoryError}</p>
                ) : categories.length === 0 ? (
                  <p>Loading categories…</p>
                ) : categories.slice(0, 5).map((row, index) => {
                  const maximum = categories[0].delivered_item_value || 1;
                  const name = categoryLabels[row.category]
                    ?? row.category.replaceAll("_", " ");
                  return (
                    <div className="category-row" key={row.category}>
                      <div className="category-row-top">
                        <span className="category-rank">{String(index + 1).padStart(2, "0")}</span>
                        <span className="category-name">{name}</span>
                        <strong>{formatMoney(row.delivered_item_value)}</strong>
                      </div>
                      <div className="bar-track">
                        <div className="bar-fill" style={{
                          width: `${(row.delivered_item_value / maximum) * 100}%`,
                          background: categoryColors[index % categoryColors.length],
                        }} />
                      </div>
                    </div>
                  );
                })}
              </div>
              <div className="panel-link" onClick={() => setActivePage("Products & categories")}>Explore all categories <span>→</span></div>
            </article>
          </div>

          <section className="panel forecast-panel">
            <div className="panel-header">
              <div>
                <h3>Revenue forecast</h3>
                <p>Four-week damped-trend projection</p>
              </div>
              <span className="forecast-badge">
                {(revenueForecast?.forecast_status ?? "historical_demo")
                  .replaceAll("_", " ")
                  .toUpperCase()}
              </span>
            </div>

            <div className="forecast-notice" role="note">
              <strong>Historical projection, not a current forecast.</strong>
              <span>
                Based on Olist data through{" "}
                {revenueForecast?.historical_cutoff
                  ? new Date(
                      `${revenueForecast.historical_cutoff.slice(0, 10)}T12:00:00`,
                    ).toLocaleDateString("en-GB", {
                      day: "numeric",
                      month: "short",
                      year: "numeric",
                    })
                  : "20 Aug 2018"}.
                Forecast dates are historical test outputs.
              </span>
            </div>

            {forecastError ? (
              <p role="alert" className="forecast-error">
                Could not load forecast: {forecastError}
              </p>
            ) : revenueForecast ? (
              <>
                <div className="forecast-metrics">
                  <div>
                    <span>Damped trend model WAPE</span>
                    <strong>{revenueForecast.evaluation.damped_trend.wape_pct.toFixed(2)}%</strong>
                  </div>
                  <div>
                    <span>Baseline WAPE</span>
                    <strong>{revenueForecast.evaluation.baseline.wape_pct.toFixed(2)}%</strong>
                  </div>
                  <div>
                    <span>Relative WAPE improvement</span>
                    <strong>
                      {(
                        (1 -
                          revenueForecast.evaluation.damped_trend.wape_pct /
                            revenueForecast.evaluation.baseline.wape_pct) *
                        100
                      ).toFixed(2)}%
                    </strong>
                  </div>
                  <div>
                    <span>Test window</span>
                    <strong>{revenueForecast.evaluation.test_weeks} weeks</strong>
                  </div>
                </div>

                <div className="forecast-chart">
                  <RevenueChart
                    option={buildForecastOption(revenueForecast.forecast)}
                    style={{ height: 250, width: "100%" }}
                    notMerge
                    lazyUpdate
                  />
                </div>

                <div className="forecast-detail-list">
                  {revenueForecast.forecast.map((row) => (
                    <div className="forecast-detail-row" key={row.week_start}>
                      <span>
                        {new Date(`${row.week_start.slice(0, 10)}T12:00:00`).toLocaleDateString(
                          "en-US",
                          { month: "short", day: "numeric", year: "numeric" },
                        )}
                      </span>
                      <strong>{formatMoney(row.forecast_revenue)}</strong>
                    </div>
                  ))}
                </div>

                <div className="chart-footer">
                  <span>Damped trend · chronological holdout evaluation</span>
                  <span>Currency: BRL</span>
                </div>
              </>
            ) : (
              <div className="chart-loading">Loading revenue forecast…</div>
            )}
          </section>

          <section className="panel customer-segments-panel">
            <div className="panel-header">
              <div>
                <h3>Customer intelligence</h3>
                <p>Customer distribution, delivered item value, and average recency by segment</p>
              </div>
              <Users size={18} className="muted-icon" />
            </div>
            <div className="retention-summary">
              <h4>90-day repeat-purchase rate</h4>
              {retentionError ? (
                <p role="alert">{retentionError}</p>
              ) : customerRetention ? (
                <>
                  <strong>
                    {Number(customerRetention.second_order_within_90_days_pct).toFixed(2)}%
                  </strong>
                  <p>
                    {customerRetention.customers_with_second_order_within_90_days.toLocaleString("en-US")} of{" "}
                    {customerRetention.eligible_customers.toLocaleString("en-US")} eligible customers placed a second recorded order within 90 days of their first.
                  </p>
                  <small>Historical Olist data · Reference date: 18 Oct 2018</small>
                </>
              ) : (
                <p>Loading 90-day retention metric…</p>
              )}
            </div>
            {segmentError ? (
              <p role="alert">{segmentError}</p>
            ) : customerSegments.length === 0 ? (
              <p>Loading customer segments…</p>
            ) : (
              <div className="segment-list">
                {customerSegments.map((segment, index) => {
                  const totalCustomers = customerSegments.reduce(
                    (total, item) => total + item.customer_count,
                    0,
                  );
                  const share = totalCustomers
                    ? (segment.customer_count / totalCustomers) * 100
                    : 0;
                  const colors = ["#2563eb", "#94a3b8", "#0d9488", "#8b5cf6"];
                  return (
                    <div className="segment-row" key={segment.segment}>
                      <div className="segment-row-heading">
                        <strong>{segment.segment}</strong>
                        <span>{segment.customer_count.toLocaleString("en-US")} customers · {share.toFixed(2)}%</span>
                      </div>
                      <div className="bar-track">
                        <div className="bar-fill" style={{
                          width: `${share}%`,
                          background: colors[index % colors.length],
                        }} />
                      </div>
                      <div className="segment-row-details">
                        <span>Delivered item value <strong>{formatMoney(segment.delivered_item_value)}</strong></span>
                        <span>Avg. recency <strong>{segment.average_recency_days == null ? "—" : `${segment.average_recency_days.toFixed(1)} days`}</strong></span>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </section>

          <div className="bottom-grid">
            <article className="panel insight-panel">
              <div className="panel-header"><div className="insight-title"><span className="insight-spark"><Sparkles size={17} /></span><div><h3>Business signal</h3><p>Evidence from your historical data</p></div></div><span className="insight-label">OPPORTUNITY</span></div>
              <h4>Customer retention deserves attention.</h4>
              <p className="insight-body">
                {kpis && customerSegments.length
                  ? `${kpis.repeat_customers.toLocaleString("en-US")} of ${kpis.unique_customers.toLocaleString("en-US")} unique customers have at least two recorded orders. The segment totals classify 18 repeat customers with no delivered orders under "No delivered order". Repeat purchasing does not by itself establish why customers return or leave.`
                  : "Loading customer metrics…"}
              </p>
              <div className="insight-metrics">
                <div><span>Repeat customers</span><strong>{kpis ? kpis.repeat_customers.toLocaleString("en-US") : "—"}</strong></div>
                <div><span>Recorded repeat rate</span><strong>{kpis ? `${kpis.repeat_customer_rate.toFixed(2)}%` : "—"}</strong></div>
                <div><span>Next investigation</span><strong>Purchase cohorts</strong></div>
              </div>
              <button className="insight-action" onClick={() => setActivePage("Customer intelligence")}>Explore customer intelligence <span>→</span></button>
            </article>
            <article className="panel regional-panel">
              <div className="panel-header"><div><h3>Regional performance</h3><p>Leading states by delivered item value</p></div><MapPinned size={18} className="muted-icon" /></div>
              {regionError ? (
                <p role="alert">{regionError}</p>
              ) : regions.length === 0 ? (
                <p>Loading regions…</p>
              ) : regions.slice(0, 3).map((row, index) => (
                <div className="region-feature" key={row.customer_state}>
                  <div className={`region-code ${index === 1 ? "region-code-alt" : ""} ${index === 2 ? "region-code-third" : ""}`}>
                    {row.customer_state}
                  </div>
                  <div className="region-copy">
                    <strong>{stateLabels[row.customer_state] ?? row.customer_state}</strong>
                    <span>{["Highest", "Second-highest", "Third-highest"][index]} delivered item value</span>
                  </div>
                  <div className="region-value">{formatMoney(row.delivered_item_value)}</div>
                </div>
              ))}
              <button className="panel-link region-link" onClick={() => setActivePage("Regional performance")}>View regional breakdown <span>→</span></button>
            </article>
          </div>

          <footer className="dashboard-footer"><span>RevenuePilot <span className="footer-separator">·</span> AI-powered revenue decision intelligence</span><span><span className="footer-status" /> Local preview <span className="footer-separator">·</span> Olist historical data</span></footer>
        </div>
      </section>
    </main>
  );
}
