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
export function AddGraph(tree){
    const el=document.getElementById("graph")
    el.innerHTML=tree;

}
export function Include(url){
    var doc = document.querySelector('link[rel="import"]').import;
    var el=doc.querySelector("html")
    var clone = document.importNode(el.content, true);
    document.getElementById("graph").appendChild(clone)
}
export function RemoveGraph(){
    const el=document.getElementById("graph");
    el.innerHTML="";
    
}