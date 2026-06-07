document.addEventListener("DOMContentLoaded", function () {
  const signupForm = document.getElementById("signupForm");
  const roleSelect = document.getElementById("floatingRole");

  roleSelect.addEventListener("change", toggleInstructorFields);

  signupForm.addEventListener("submit", function (event) {
    if (roleSelect.value === "") {
      event.preventDefault();
      roleSelect.classList.add("is-invalid");
      roleSelect.focus();
    } else {
      roleSelect.classList.remove("is-invalid");
    }
  });
});

function toggleInstructorFields() {
  const roleSelect = document.getElementById("floatingRole");
  const instructorFields = document.getElementById("instructorFields");
  const especialidadInput = document.getElementById("floatingEspecialidad");
  const biografiaInput = document.getElementById("floatingBiografia");

  if (roleSelect.value === "instructor") {
    instructorFields.style.display = "block";
    especialidadInput.setAttribute("required", "true");
    biografiaInput.setAttribute("required", "true");
  } else {
    instructorFields.style.display = "none";
    especialidadInput.removeAttribute("required");
    biografiaInput.removeAttribute("required");
    especialidadInput.value = "";
    biografiaInput.value = "";

    if (roleSelect.value !== "") {
      roleSelect.classList.remove("is-invalid");
    }
  }
}
