(() => {
    const imageInput = document.querySelector('input[type="file"][name="images"]');
    const status = document.querySelector("[data-image-upload-status]");
    const preview = document.querySelector("[data-image-preview]");

    if (!imageInput || !status || !preview) {
        return;
    }

    let selectedFiles = [];
    let objectUrls = new Map();
    let statusTimer = null;

    const fileKey = (file) => `${file.name}:${file.size}:${file.lastModified}`;

    const imageLabel = (count) => {
        if (count === 0) {
            return status.dataset.emptyLabel || "";
        }

        if (count === 1) {
            return status.dataset.singleLabel || "1 image selected.";
        }

        const multipleLabel = status.dataset.multipleLabel || "images selected.";
        return `${count} ${multipleLabel}`;
    };

    const duplicateLabel = (count) => {
        if (count === 1) {
            return status.dataset.duplicateLabel || "Bilden är redan tillagd.";
        }

        return status.dataset.duplicatesLabel || "Bilderna är redan tillagda.";
    };

    const setStatus = (message) => {
        status.textContent = message;
    };

    const setTemporaryStatus = (message) => {
        window.clearTimeout(statusTimer);
        setStatus(message);

        statusTimer = window.setTimeout(() => {
            setStatus(imageLabel(selectedFiles.length));
        }, 2200);
    };

    const syncInputFiles = () => {
        const dataTransfer = new DataTransfer();

        for (const file of selectedFiles) {
            dataTransfer.items.add(file);
        }

        imageInput.files = dataTransfer.files;
    };

    const releaseObjectUrl = (key) => {
        const objectUrl = objectUrls.get(key);

        if (!objectUrl) {
            return;
        }

        URL.revokeObjectURL(objectUrl);
        objectUrls.delete(key);
    };

    const clearAllObjectUrls = () => {
        for (const objectUrl of objectUrls.values()) {
            URL.revokeObjectURL(objectUrl);
        }

        objectUrls.clear();
    };

    const renderPreview = () => {
        preview.replaceChildren();
        setStatus(imageLabel(selectedFiles.length));

        for (const file of selectedFiles) {
            if (!file.type.startsWith("image/")) {
                continue;
            }

            const key = fileKey(file);
            let objectUrl = objectUrls.get(key);

            if (!objectUrl) {
                objectUrl = URL.createObjectURL(file);
                objectUrls.set(key, objectUrl);
            }

            const item = document.createElement("div");
            item.className = "write-form__image-preview-item";

            const image = document.createElement("img");
            image.src = objectUrl;
            image.alt = file.name;
            image.loading = "lazy";

            const removeButton = document.createElement("button");
            removeButton.className = "write-form__image-preview-remove";
            removeButton.type = "button";
            removeButton.setAttribute("aria-label", `Ta bort ${file.name}`);
            removeButton.textContent = "×";

            removeButton.addEventListener("click", () => {
                selectedFiles = selectedFiles.filter(
                    (selectedFile) => fileKey(selectedFile) !== key
                );

                releaseObjectUrl(key);
                syncInputFiles();
                renderPreview();
            });

            item.appendChild(image);
            item.appendChild(removeButton);
            preview.appendChild(item);
        }
    };

    imageInput.addEventListener("change", () => {
        const existingKeys = new Set(selectedFiles.map(fileKey));
        const newFiles = Array.from(imageInput.files || []);
        let duplicateCount = 0;

        for (const file of newFiles) {
            if (!file.type.startsWith("image/")) {
                continue;
            }

            const key = fileKey(file);

            if (existingKeys.has(key)) {
                duplicateCount += 1;
                continue;
            }

            selectedFiles.push(file);
            existingKeys.add(key);
        }

        syncInputFiles();
        renderPreview();

        if (duplicateCount > 0) {
            setTemporaryStatus(duplicateLabel(duplicateCount));
        }
    });

    window.addEventListener("beforeunload", () => {
        window.clearTimeout(statusTimer);
        clearAllObjectUrls();
    });
})();
