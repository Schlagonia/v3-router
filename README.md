# V2 Base Strategy Adapter

This repo is to allow you to write a strategy for YearnV3 that will work with a Yearn V2 vault.

All adaptations are already implemented in BaseStrategyAdapter.sol.

You will only need to override the functions in Strategy.sol of '_deployFunds', '_freeFunds', '_harvestAndReport' and '_emergencyWithdraw'. With the option to also override '_tend' and 'tendTrigger' if needed.

NOTE: This cannot be used for V2 Gen lender plugins. Plugins should be ported completely to V3 and not use an adapter using the [Tokenized Strategy Ape Mix](https://github.com/Schlagonia/tokenized-strategy-ape-mix).

## Using Brownie

This repo utilizes Ape Worx, however the adapter can also be used in an existing Brownie repositories in order to not have to migrate tests.

Simply copy and paste the `Strategy.sol` and `BaseStrategyAdapter.sol` contracts into your Brownie repo in replace of the current Strategy.sol contract and continue to override the same functions you otherwise would have. All existing tests should function properly if logic is implemented properly.

NOTE: You will need to adjust the import path on line 8 of `BaseStrategyAdapter.sol` for the Brownie specific dependencies.

## How to start using Ape

### Fork this repo

    git clone https://github.com/user/V2-Base-Strategy-Adapter

    cd V2-Base-Strategy-Adapter

### Set up your virtual enviorment

    python3 -m venv venv

    source venv/bin/acitvate

### Install Ape and all dependencies

    pip install -r requirements.txt
    
    yarn
    
    ape plugins install .
    
    ape compile
    
    ape test
    
### Set your enviorment Variables

    export WEB3_INFURA_PROJECT_ID=yourInfuraApiKey

See the ApeWorx [documentation](https://docs.apeworx.io/ape/stable/) and [github](https://github.com/ApeWorX/ape) for more information.