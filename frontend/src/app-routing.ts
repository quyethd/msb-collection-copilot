export type AppPage = 'overview'|'priority'|'customer'|'impact'|'zalo';

const PATHS: Record<AppPage,string> = {
  overview: '/app', priority: '/app/priority', customer: '/app/customer',
  impact: '/app/impact', zalo: '/app/zalo',
};

export const pageFromPath = (pathname:string):AppPage =>
  (Object.entries(PATHS).find(([,path])=>path===pathname)?.[0] as AppPage) || 'overview';

export const pathForPage = (page:AppPage):string => PATHS[page];
