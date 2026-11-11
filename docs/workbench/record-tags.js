/* Shared normalization for editor inputs and Workbench tag filters. */
(() => {
 'use strict';
 const maxTags=30;
 function normalize(value){
  const key=String(value??'').normalize('NFKC').trim().replace(/^#/,'').trim().toLowerCase().replace(/\s+/gu,'-');
  return [...key].length<=64&&/^[\p{L}\p{N}][\p{L}\p{M}\p{N}_-]*$/u.test(key)?key:'';
 }
 function keys(values){
  return [...new Set(values.map(normalize).filter(Boolean))].sort().slice(0,maxTags);
 }
 function search(value){
  // Treat unquoted, whitespace-delimited hashtags as exact tag filters.
  const tags=[];
  const query=value.replace(/"[^"]*"|\S+/gu,part=>{
   if(!part.startsWith('#'))return part;
   const tag=normalize(part);
   if(!tag)return part;
   tags.push(tag);return '';
  }).trim();
  return {query,tags:keys(tags)};
 }
 window.SCRO_RECORD_TAGS=Object.freeze({normalize,keys,search,maxTags});
})();
