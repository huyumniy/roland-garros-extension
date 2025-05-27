export const fetchData = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      method: "GET",
      headers: {
        "x-queueit-ajaxpageurl": encodeURIComponent(window.location.href),
        ...options.headers,
      },
    });
    if (!response.ok) {
      throw new Error(`Response status: ${response.status}`);
    }

    const json = await response.json();
    console.log(json);
  } catch (error) {
    console.error(error.message);
  }
};

export const postData = async (url, data, options = {}) => {
  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        "x-queueit-ajaxpageurl": encodeURIComponent(window.location.href),
        "Content-Type": "application/json",
        ...options.headers,
      },
      body: JSON.stringify(data),
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const responseData = await response.json();
    return responseData;
  } catch (error) {
    console.error("Error posting data:", error);
    throw error; // Re-throw the error for further handling if needed
  }
};
