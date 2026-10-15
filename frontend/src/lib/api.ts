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
