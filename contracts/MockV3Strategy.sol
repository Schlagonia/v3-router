// SPDX-License-Identifier: GPL-3.0
pragma solidity 0.8.18;

import {BaseStrategy} from "@tokenized-strategy/BaseStrategy.sol";

import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract MockV3Strategy is BaseStrategy {
    using SafeERC20 for ERC20;

    uint256 public withdrawable = type(uint256).max;

    constructor(
        address _asset,
        string memory _name
    ) BaseStrategy(_asset, _name) {}

    function _deployFunds(uint256 _amount) internal override {}

    function _freeFunds(uint256 _amount) internal override {}

    function _harvestAndReport()
        internal
        override
        returns (uint256 _totalAssets)
    {
        _totalAssets = asset.balanceOf(address(this));
    }

    function availableWithdrawLimit(
        address
    ) public view override returns (uint256) {
        return withdrawable;
    }

    function setWithdrawable(uint256 _withdrawable) external {
        withdrawable = _withdrawable;
    }
}
