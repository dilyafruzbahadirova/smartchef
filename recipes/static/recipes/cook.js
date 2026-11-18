"use strict";
document.addEventListener("DOMContentLoaded", () => {
 const root=document.getElementById("cooking-app");if(!root)return;
 const data=JSON.parse(document.getElementById("cooking-recipe-data").textContent);
 const steps=data.steps,ru=root.dataset.language==="ru";
 let current=0;const completed=new Set();let finished=false;
 const el=id=>document.getElementById(id);
 function render(){
  el("step-panel").hidden=finished;el("finish-panel").hidden=!finished;
  el("step-count").textContent=finished?(ru?"Завершено":"Аяқталды"):(ru?`Шаг ${current+1} / ${steps.length}`:`Қадам ${current+1} / ${steps.length}`);
  el("done-count").textContent=(ru?"Выполнено: ":"Орындалды: ")+completed.size+" / "+steps.length;
  el("progress-fill").style.width=(completed.size/steps.length*100)+"%";
  if(!finished){el("step-label").textContent=(ru?"ШАГ ":"ҚАДАМ ")+(current+1);el("step-description").textContent=steps[current];el("step-back").textContent=ru?"← Назад":"← Артқа";el("step-back").disabled=current===0;el("step-confirm").textContent=completed.has(current)?(ru?"Далее →":"Келесі →"):(current===steps.length-1?(ru?"Завершить ✓":"Аяқтау ✓"):(ru?"Готово, следующий шаг →":"Дайын, келесі қадам →"));}
  const list=el("steps-list");list.replaceChildren();steps.forEach((step,i)=>{const li=document.createElement("li");li.className=(completed.has(i)?"is-done ":"")+(i===current&&!finished?"is-current":"");const b=document.createElement("b");b.textContent=completed.has(i)?"✓":String(i+1);const span=document.createElement("span");span.textContent=step;li.append(b,span);list.append(li);});
 }
 el("step-back").addEventListener("click",()=>{if(current>0)current--;render();});
 el("step-confirm").addEventListener("click",()=>{completed.add(current);if(current===steps.length-1){finished=true;}else{current++;}render();});
 el("step-restart").addEventListener("click",()=>{current=0;completed.clear();finished=false;render();});render();
});
