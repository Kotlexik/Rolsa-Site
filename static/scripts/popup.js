document.addEventListener('DOMContentLoaded', function () {

    if(localStorage.getItem('popState') != 'shown'){
        const popupOverlay = document.getElementById('popupOverlay');
        const popup = document.getElementById('popup');
        const closePopup = document.getElementById('closePopup');

        function openPopup() {
            popupOverlay.style.display = 'block';
        }
        localStorage.setItem('popState','shown')
    }

        function closePopupFunc() {
            popupOverlay.style.display = 'none';
        }
        openPopup();
        closePopup.addEventListener('click', closePopupFunc);
        popupOverlay.addEventListener('click', function (event) {
            if (event.target === popupOverlay) {
                closePopupFunc();
            }
        });
});