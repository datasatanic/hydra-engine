export function ResizeMenu(x,element){
    if(x>=460 && x<=window.innerWidth*0.7){
        element.style.width=x+"px";
        const search=document.getElementById("tree-search");
        search.style.width=x-160+"px";
    }
    
}