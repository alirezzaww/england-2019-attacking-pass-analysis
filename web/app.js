'use strict';
async function start(){
  const response=await fetch('research.json');
  if(!response.ok)throw new Error('Research data could not be loaded');
  const data=await response.json();
  const names=['Francesca Kirby','Nikita Parris','Keira Walsh','Lucy Bronze'];
  const renderThreshold=threshold=>{
    const suffix=threshold==='0.07'?'007':'010';
    document.querySelectorAll('[data-threshold]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.threshold===threshold)));
    document.getElementById('selection-total').textContent=`${data.totals[threshold]} qualifying passes across seven games`;
    const body=document.getElementById('player-rows');body.replaceChildren();
    names.forEach(name=>{
      const player=data.players.find(row=>row.player_name===name);
      const tr=document.createElement('tr');
      [name,String(player[`count_${suffix}`]),player[`per90_${suffix}`].toFixed(2)].forEach(value=>{const td=document.createElement('td');td.textContent=value;tr.append(td);});body.append(tr);
    });
  };
  document.querySelectorAll('[data-threshold]').forEach(button=>button.addEventListener('click',()=>renderThreshold(button.dataset.threshold)));
  renderThreshold('0.10');
  const svg=document.getElementById('hero-pitch');
  const ns='http://www.w3.org/2000/svg';
  const element=(tag,attributes)=>{const node=document.createElementNS(ns,tag);Object.entries(attributes).forEach(([key,value])=>node.setAttribute(key,String(value)));return node;};
  data.zone_rates.forEach((row,i)=>row.forEach((value,j)=>{
    svg.append(element('rect',{x:10+j*56.6,y:10+i*44,width:56.6,height:44,fill:'#24658a','fill-opacity':0.04+value/3*0.87}));
    if(value>=1.5){const label=element('text',{x:38.3+j*56.6,y:36+i*44,'text-anchor':'middle','font-family':'Arial','font-size':12,fill:value>=2?'#fff':'#172d3b'});label.textContent=value.toFixed(1);svg.append(label);}
  }));
  [['rect',{x:10,y:10,width:339.6,height:220}],['line',{x1:179.8,y1:10,x2:179.8,y2:230}],['circle',{cx:179.8,cy:120,r:30}],['rect',{x:10,y:70,width:47,height:100}],['rect',{x:302.6,y:70,width:47,height:100}]].forEach(([tag,attributes])=>svg.append(element(tag,{...attributes,fill:'none',stroke:'#476374','stroke-width':1.2})));
  const range=document.getElementById('distance');
  range.min=String(Math.ceil(data.model.training_distance_range[0]*2)/2);
  range.max=String(Math.floor(data.model.training_distance_range[1]*2)/2);
  const renderProbability=()=>{
    const distance=Number(range.value);
    const z=data.model.intercept_scaled+data.model.distance_coefficient_scaled*(distance-data.model.training_mean_distance)/data.model.training_scale_distance;
    const probability=1/(1+Math.exp(-z));
    document.getElementById('distance-value').value=distance.toFixed(1);
    document.getElementById('xg-value').textContent=`${(probability*100).toFixed(1)}%`;
    document.getElementById('probability-bar').style.width=`${probability*100}%`;
  };
  range.addEventListener('input',renderProbability);renderProbability();
}
start().catch(error=>{
  document.getElementById('selection-total').textContent='Interactive data unavailable. The charts and repository retain the full findings.';
  document.getElementById('xg-value').textContent='Unavailable';
  console.error(error.message);
});
