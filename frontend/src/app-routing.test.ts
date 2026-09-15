import {describe,expect,it} from 'vitest';
import {pageFromPath,pathForPage} from './app-routing';

describe('authenticated application routing',()=>{
  const routes=[
    ['/app','overview'], ['/app/priority','priority'], ['/app/customer','customer'],
    ['/app/impact','impact'], ['/app/zalo','zalo'],
  ] as const;

  it('treats Zalo as a first-class route alongside the operational pages',()=>{
    for(const [path,page] of routes){
      expect(pageFromPath(path)).toBe(page);
      expect(pathForPage(page)).toBe(path);
    }
  });

  it('falls back safely for unknown application paths',()=>{
    expect(pageFromPath('/app/unknown')).toBe('overview');
  });
});
