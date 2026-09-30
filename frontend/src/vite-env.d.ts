/// <reference types="vite/client" />

declare module "*.jsx" {
  import React from "react";
  const Component: React.ComponentType<any>;
  export default Component;
  export const CampaignDashboard: React.ComponentType<any>;
  export const CampaignChart: React.ComponentType<any>;
  export const AnomalyAlerts: React.ComponentType<any>;
  export const BudgetOptimizer: React.ComponentType<any>;
}

declare module "*CampaignDashboard*" {
  import React from "react";
  export const CampaignDashboard: React.ComponentType<any>;
  export default CampaignDashboard;
}
