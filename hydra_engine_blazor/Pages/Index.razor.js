export function Scroll(){
    const id=window.location.hash
    const scrollTarget = document.getElementById(id);
    if(scrollTarget !== null){
        scrollTarget.scrollIntoView({
            behavior:"smooth",
            block:"start"
        });
    }
    
}
export function AddGraph(svg){
    const el=document.getElementById("graph")
    el.innerHTML=svg
}