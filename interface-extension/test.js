const { Configuration, NopeCHAApi } = require("nopecha");

const configuration = new Configuration({
    apiKey: "sub_1QsSuQCRwBwvt6ptjP0yralq",
});
const nopecha = new NopeCHAApi(configuration);


(async () => {
    // solve a token
    const token = await nopecha.solveToken({
        type: 'recaptcha2',
        sitekey: '6Ld8NA8jAAAAAPJ_ahIPVIMc0C4q58rntFkopFiA',
        url: 'https://nopecha.com/demo/recaptcha#easy',
    });

    // print the token
    console.log(token);

    // get the current balance
    const balance = await nopecha.getBalance();

    // print the current balance
    console.log(balance);

})()