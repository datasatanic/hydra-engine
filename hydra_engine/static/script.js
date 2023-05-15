function highlightDifferences(element1, element2) {
    // Если оба элемента существуют
    if (element1 && element2) {
        // Сравнить значения элементов
        if (element1.textContent !== element2.textContent) {
            if (element1.tagName === "H5" && element2.tagName === "H5"){
                element1.style.color = 'red';
                element2.style.color = 'green';
            }
            else if(element1.tagName!=="H5" && element2.tagName === "H5"){
                element1.style.color = 'red';
                element2.style.color = 'green';
            }
            else if (element1.tagName==="H5" && element2.tagName !== "H5"){
                element1.style.color = 'red';
                element2.style.color = 'green';
            }
        }

        // Рекурсивно проверить дочерние элементы
        const children1 = element1.children;
        const children2 = element2.children;
        for (let i = 0; i < children1.length; i++) {
            highlightDifferences(children1[i], children2[i]);
        }
    }
    // Если только первый элемент существует
    else if (element1) {
        element1.style.color = 'red';
        
    }
    // Если только второй элемент существует
    else if (element2) {
        element2.style.color = 'green';
        
    }
}
window.onload=function (){
    let old_values=document.querySelector(".old-values>.resource-changes-container")
    let new_values=document.querySelector(".new-values>.resource-changes-container")
    highlightDifferences(old_values,new_values)
}
