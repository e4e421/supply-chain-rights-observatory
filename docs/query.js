/* Deterministic local search over already published metadata.
   Plain tokens are ANDed; explicit OR divides groups; quoted phrases are exact.
   No eval, regex evaluation of user strings, network calls or data collection. */
(() => {
'use strict';
function tokenize(source){
  const input=String(source||'').trim().slice(0,120);
  return (input.match(/"[^"]+"|\S+/g)||[]).slice(0,24);
}
function matches(text,query){
 const tokens=tokenize(query);
 if(!tokens.length)return true;
 const content=String(text||'').toLocaleLowerCase();
 const groups=[[]];
 for(let token of tokens){
  if(/^OR$/i.test(token)){if(groups[groups.length-1].length)groups.push([]);continue;}
  if(/^AND$/i.test(token))continue;
  token=token.replace(/^"|"$/g,'').toLocaleLowerCase();
  if(token)groups[groups.length-1].push(token);
 }
 return groups.some(group=>group.length>0 && group.every(x=>content.includes(x)));
}
window.SCRO_QUERY=Object.freeze({matches,tokenize});
})();