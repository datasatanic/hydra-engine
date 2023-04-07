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
    let frame=document.createElement("iframe");
    frame.src="plan/index.html";
    frame.style.width="90vw";
    frame.style.height="90vh"
    el.appendChild(frame)

}
export function Include(url){
    var doc = document.querySelector('link[rel="import"]').import;
    var el=doc.querySelector("html")
    var clone = document.importNode(el.content, true);
    document.getElementById("graph").appendChild(clone)
}