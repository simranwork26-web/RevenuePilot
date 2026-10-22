const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000";

export type DashboardKpis = {
  total_orders: number;
  delivered_orders: number;
  unique_customers: number;
  delivered_item_value: number;
  repeat_customers: number;
  segmented_customers: number;
  repeat_customer_rate: number;
};

export type MonthlyRevenue = {
  month: string;
  order_count: number;
  delivered_order_count: number;
  item_value_total: number;
  delivered_item_value: number;
  recorded_payment_value_total: number;
  low_volume_month: boolean;
};

export type CategoryMetric = {
  category: string;
  item_count: number;
  order_count: number;
  delivered_item_count: number;
  delivered_order_count: number;
  item_value_total: number;
  delivered_item_value: number;
};

export type RegionMetric = {
  customer_state: string;
  order_count: number;
  delivered_order_count: number;
  unique_customer_count: number;
  item_value_total: number;
  delivered_item_value: number;
  freight_value_total: number;
  average_delivered_item_value_per_order: number | null;
};

export type CustomerSegment = {
  segment: string;
  customer_count: number;
  delivered_item_value: number;
  average_recency_days: number | null;
};

async function fetchApi<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`API request failed (${response.status}): ${path}`);
  }

  return response.json() as Promise<T>;
}

export const getDashboardKpis = () =>
  fetchApi<DashboardKpis>("/api/kpis");

export const getMonthlyRevenue = () =>
  fetchApi<MonthlyRevenue[]>("/api/revenue/monthly");

export const getCategories = () =>
  fetchApi<CategoryMetric[]>("/api/categories");

export const getRegions = () =>
  fetchApi<RegionMetric[]>("/api/regions");

export const getCustomerSegments = () =>
  fetchApi<CustomerSegment[]>("/api/customers/segments");

export type CustomerRetention = {
  eligible_customers: number;
  customers_with_second_order_within_90_days: number;
  second_order_within_90_days_pct: number | string;
};

export const getCustomerRetention = () =>
  fetchApi<CustomerRetention>("/api/customers/retention");

export type CustomerCohort = {
  cohort_month: string;
  cohort_size: number;
  retention: Record<string, number>;
};

export type CustomerCohortRetention = {
  reference_date: string;
  historical_cutoff: string | null;
  cohort_count: number;
  cohorts: CustomerCohort[];
};

export const getCustomerCohorts = () =>
  fetchApi<CustomerCohortRetention>("/api/customers/cohorts");


export type RetentionCohortSummary = {
  cohort_month: string;
  cohort_size: number;
  retention_pct: number;
};

export type ComparableRetention = {
  month_number: number;
  cohort_count: number;
  average_retention_pct: number;
  highest: RetentionCohortSummary;
  lowest: RetentionCohortSummary;
  status: "no_observed_repeat_activity" | "retention_observed";
  interpretation: string;
};

export type CustomerRetentionInsights = {
  minimum_cohort_size: number;
  small_cohort_count: number;
  small_cohorts: {
    cohort_month: string;
    cohort_size: number;
  }[];
  comparable_retention: ComparableRetention | null;
};

export const getCustomerRetentionInsights = () =>
  fetchApi<CustomerRetentionInsights>("/api/customers/retention-insights");

export type ForecastMetrics = {
  mae: number;
  rmse: number;
  wape_pct: number;
};

export type RevenueForecast = {
  forecast_horizon_weeks: number;
  revenue_metric: string;
  currency: string;
  historical_cutoff: string;
  forecast_status: "historical_demo" | string;
  evaluation: {
    training_weeks: number;
    test_weeks: number;
    training_start: string;
    training_end: string;
    test_start: string;
    test_end: string;
    baseline: ForecastMetrics;
    damped_trend: ForecastMetrics;
  };
  forecast: {
    week_start: string;
    forecast_revenue: number;
  }[];
};

export const getRevenueForecast = () =>
  fetchApi<RevenueForecast>("/api/revenue/forecast");


export type RevenueBridge = {
  previous_month: string;
  current_month: string;
  previous_revenue: number;
  current_revenue: number;
  revenue_change: number;
  revenue_change_pct: number | null;
  previous_delivered_orders: number;
  current_delivered_orders: number;
  previous_average_order_value: number;
  current_average_order_value: number;
  volume_impact: number;
  average_order_value_impact: number;
};

export type RevenueDriver = {
  category?: string;
  customer_state?: string;
  previous_revenue: number;
  current_revenue: number;
  revenue_change: number;
};

export type RevenueDriverDrilldown = {
  previous_month: string;
  current_month: string;
  previous_revenue: number;
  current_revenue: number;
  revenue_change: number;
  category_drivers: RevenueDriver[];
  regional_drivers: RevenueDriver[];
};

export const getRevenueDriverDrilldown = (
  previousMonth: string,
  currentMonth: string,
) =>
  fetchApi<RevenueDriverDrilldown>(
    `/api/revenue/drivers?previous_month=${encodeURIComponent(previousMonth)}&current_month=${encodeURIComponent(currentMonth)}`,
  );

export const getRevenueBridge = (
  previousMonth: string,
  currentMonth: string,
) =>
  fetchApi<RevenueBridge>(
    `/api/revenue/bridge?previous_month=${encodeURIComponent(previousMonth)}&current_month=${encodeURIComponent(currentMonth)}`,
  );
