(function () {
    const lightbox = document.querySelector("[data-gallery-lightbox]");

    if (!lightbox) {
        return;
    }

    const image = lightbox.querySelector(".gallery-lightbox__image");
    const caption = lightbox.querySelector("[data-gallery-caption]");
    const count = lightbox.querySelector("[data-gallery-count]");
    const prevButton = lightbox.querySelector("[data-gallery-prev]");
    const nextButton = lightbox.querySelector("[data-gallery-next]");

    let images = [];
    let currentIndex = 0;

    function readGallery(galleryId) {
        const gallery = document.getElementById(galleryId);

        if (!gallery) {
            return [];
        }

        return Array.from(gallery.querySelectorAll("a")).map((link) => {
            return {
                src: link.href,
                alt: link.dataset.alt || "",
                caption: link.dataset.caption || "",
            };
        });
    }

    function showImage(index) {
        if (images.length === 0) {
            return;
        }

        currentIndex = (index + images.length) % images.length;

        const currentImage = images[currentIndex];

        image.src = currentImage.src;
        image.alt = currentImage.alt;
        caption.textContent = currentImage.caption;
        count.textContent = `${currentIndex + 1} / ${images.length}`;

        const hasMultipleImages = images.length > 1;
        prevButton.hidden = !hasMultipleImages;
        nextButton.hidden = !hasMultipleImages;
    }

    function openLightbox(galleryId) {
        images = readGallery(galleryId);

        if (images.length === 0) {
            return;
        }

        lightbox.hidden = false;
        lightbox.setAttribute("aria-hidden", "false");
        document.body.style.overflow = "hidden";

        showImage(0);
        nextButton.focus();
    }

    function closeLightbox() {
        lightbox.hidden = true;
        lightbox.setAttribute("aria-hidden", "true");
        document.body.style.overflow = "";

        image.src = "";
        image.alt = "";
        caption.textContent = "";
        count.textContent = "";

        images = [];
        currentIndex = 0;
    }

    document.addEventListener("click", function (event) {
        const trigger = event.target.closest("[data-gallery-trigger]");

        if (trigger) {
            openLightbox(trigger.dataset.galleryId);
            return;
        }

        if (event.target.closest("[data-gallery-close]")) {
            closeLightbox();
            return;
        }

        if (event.target.closest("[data-gallery-prev]")) {
            showImage(currentIndex - 1);
            return;
        }

        if (event.target.closest("[data-gallery-next]")) {
            showImage(currentIndex + 1);
        }
    });

    document.addEventListener("keydown", function (event) {
        if (lightbox.hidden) {
            return;
        }

        if (event.key === "Escape") {
            closeLightbox();
            return;
        }

        if (event.key === "ArrowLeft") {
            showImage(currentIndex - 1);
            return;
        }

        if (event.key === "ArrowRight") {
            showImage(currentIndex + 1);
        }
    });
})();
