"use client";

import dynamic from "next/dynamic";
import { useState } from "react";
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

const revenueOption = {
  animationDuration: 650,
  tooltip: {
    trigger: "axis",
    backgroundColor: "#142d4e",
    borderWidth: 0,
    textStyle: { color: "#ffffff" },
    formatter: (params: { axisValue: string; value: number }[]) =>
      `${params[0].axisValue}<br/><strong>₹${params[0].value.toLocaleString("en-IN")}</strong>`,
  },
  grid: { left: 8, right: 12, top: 20, bottom: 8, containLabel: true },
  xAxis: {
    type: "category",
    boundaryGap: false,
    data: ["May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
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
        value === 0 ? "0" : `${(value / 100000).toFixed(0)}L`,
    },
    splitLine: { lineStyle: { color: "#edf1f6", type: "dashed" } },
  },
  series: [
    {
      name: "Item value",
      type: "line",
      smooth: 0.35,
      symbol: "circle",
      symbolSize: 7,
      data: [420000, 510000, 475000, 620000, 570000, 710000, 665000, 820000],
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
};

const categoryRows = [
  { name: "Health & beauty", value: 1233131.72, share: 100, color: "#2563eb" },
  { name: "Watches & gifts", value: 1166176.98, share: 94.6, color: "#6092ed" },
  { name: "Bed & bath table", value: 1023434.76, share: 83, color: "#8bb0f5" },
  { name: "Sports & leisure", value: 954852.55, share: 77.4, color: "#b3caf7" },
  { name: "Computers & accessories", value: 888724.61, share: 72.1, color: "#d1def8" },
];

const formatMoney = (value: number) =>
  new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 0,
  }).format(value);

export default function Home() {
  const [theme, setTheme] = useState("executive");
  const [activePage, setActivePage] = useState("Overview");
  const [showThemes, setShowThemes] = useState(false);
  const [mobileMenu, setMobileMenu] = useState(false);

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
            <div><strong>Historical dataset preview</strong><span>Figures are based on the Olist dataset period. Some chart values are illustrative until the live data connection is implemented.</span></div>
            <span className="notice-tag">PREVIEW</span>
          </div>

          <div className="section-heading">
            <div><h2>Performance snapshot</h2><p>Your key business indicators at a glance</p></div>
            <span className="period-pill"><span /> Historical period</span>
          </div>

          <div className="kpi-grid">
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Delivered item value</span><span className="kpi-icon blue"><CreditCard size={18} /></span></div>
              <div className="kpi-value">{formatMoney(13221498.11)}</div>
              <div className="kpi-foot"><span className="kpi-neutral">Historical total</span><span className="kpi-caption">Delivered orders only</span></div>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Delivered orders</span><span className="kpi-icon violet"><ShoppingCart size={18} /></span></div>
              <div className="kpi-value">96,478</div>
              <div className="kpi-foot"><span className="kpi-neutral">Historical total</span><span className="kpi-caption">Of 99,441 orders</span></div>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Unique customers</span><span className="kpi-icon teal"><Users size={18} /></span></div>
              <div className="kpi-value">96,096</div>
              <div className="kpi-foot"><span className="kpi-neutral">Historical total</span><span className="kpi-caption">Distinct customer IDs</span></div>
            </article>
            <article className="kpi-card">
              <div className="kpi-top"><span className="kpi-label">Repeat customer rate</span><span className="kpi-icon amber"><Activity size={18} /></span></div>
              <div className="kpi-value">3.12<span className="value-unit">%</span></div>
              <div className="kpi-foot"><span className="kpi-insight"><ArrowDownRight size={14} /> Retention opportunity</span><span className="kpi-caption">2,997 repeat customers</span></div>
            </article>
          </div>

          <div className="charts-grid">
            <article className="panel revenue-panel">
              <div className="panel-header">
                <div><h3>Revenue performance</h3><p>Monthly item value trend</p></div>
                <button className="select-button">Monthly <ChevronDown size={14} /></button>
              </div>
              <div className="chart-legend"><span /><span>Item value</span><small>Illustrative trend · not connected to live monthly data</small></div>
              <RevenueChart option={revenueOption} style={{ height: 275, width: "100%" }} notMerge lazyUpdate />
              <div className="chart-footer"><span><i /> Historical trend preview</span><span>Values shown in INR</span></div>
            </article>

            <article className="panel category-panel">
              <div className="panel-header"><div><h3>Top product categories</h3><p>By delivered item value</p></div><button className="more-button" aria-label="More category options">···</button></div>
              <div className="category-total">{formatMoney(1233131.72)}<span>Top category</span></div>
              <div className="category-list">
                {categoryRows.map((row, index) => (
                  <div className="category-row" key={row.name}>
                    <div className="category-row-top"><span className="category-rank">{String(index + 1).padStart(2, "0")}</span><span className="category-name">{row.name}</span><strong>{formatMoney(row.value)}</strong></div>
                    <div className="bar-track"><div className="bar-fill" style={{ width: `${row.share}%`, background: row.color }} /></div>
                  </div>
                ))}
              </div>
              <div className="panel-link" onClick={() => setActivePage("Products & categories")}>Explore all categories <span>→</span></div>
            </article>
          </div>

          <div className="bottom-grid">
            <article className="panel insight-panel">
              <div className="panel-header"><div className="insight-title"><span className="insight-spark"><Sparkles size={17} /></span><div><h3>Business signal</h3><p>Evidence from your historical data</p></div></div><span className="insight-label">OPPORTUNITY</span></div>
              <h4>Customer retention deserves attention.</h4>
              <p className="insight-body">2,997 of 96,096 unique customers have at least two recorded orders. This suggests a potential area to investigate, but the metric alone does not explain why customers do not return.</p>
              <div className="insight-metrics"><div><span>Repeat customers</span><strong>2,997</strong></div><div><span>Recorded repeat rate</span><strong>3.12%</strong></div><div><span>Next investigation</span><strong>Purchase cohorts</strong></div></div>
              <button className="insight-action" onClick={() => setActivePage("Customer intelligence")}>Explore customer intelligence <span>→</span></button>
            </article>
            <article className="panel regional-panel">
              <div className="panel-header"><div><h3>Regional performance</h3><p>Leading states by delivered item value</p></div><MapPinned size={18} className="muted-icon" /></div>
              <div className="region-feature"><div className="region-code">SP</div><div className="region-copy"><strong>São Paulo</strong><span>Highest delivered item value</span></div><div className="region-value">{formatMoney(5067633.16)}</div></div>
              <div className="region-feature"><div className="region-code region-code-alt">RJ</div><div className="region-copy"><strong>Rio de Janeiro</strong><span>Second-highest state</span></div><div className="region-value">{formatMoney(1759651.13)}</div></div>
              <div className="region-feature"><div className="region-code region-code-third">MG</div><div className="region-copy"><strong>Minas Gerais</strong><span>Third-highest state</span></div><div className="region-value">{formatMoney(1552481.83)}</div></div>
              <button className="panel-link region-link" onClick={() => setActivePage("Regional performance")}>View regional breakdown <span>→</span></button>
            </article>
          </div>

          <footer className="dashboard-footer"><span>RevenuePilot <span className="footer-separator">·</span> AI-powered revenue decision intelligence</span><span><span className="footer-status" /> Local preview <span className="footer-separator">·</span> Olist historical data</span></footer>
        </div>
      </section>
    </main>
  );
}
