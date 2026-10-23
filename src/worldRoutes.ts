import geography from '../design/rongguo-world.json' with {type:'json'};
export type Cell={col:number;row:number};
const nodes=geography.network.nodes as Record<string,number[]>;
export function worldRouteCells(from:string,to:string):Cell[]{
  const find=(a:string,b:string)=>{
    const queue=[[a]],seen=new Set([a]);
    while(queue.length){const path=queue.shift()!,last=path.at(-1)!;if(last===b)return path;
      for(const edge of geography.network.edges){const next=edge[0]===last?edge[1]:edge[1]===last?edge[0]:null;if(next&&!seen.has(next)){seen.add(next);queue.push([...path,next]);}}
    }return [];
  };
  if(!nodes[from]||!nodes[to])return [];
  // The third-chapter visit explicitly exits the west gate before passing the main gate.
  const via=(to==='east'&&['entry','dinner','night','feng'].includes(from))||
    (from==='east'&&['entry','dinner','night','feng'].includes(to))?'capital':null;
  const ids=via?[...find(from,via),...find(via,to).slice(1)]:find(from,to);
  return ids.map(id=>({col:nodes[id][0],row:nodes[id][1]}));
}
export const worldRoadSegments=geography.network.edges.map(([a,b])=>[nodes[a],nodes[b]].map(([col,row])=>({col,row})));
