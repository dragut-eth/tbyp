// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";


contract TBYPToken is ERC20, Ownable {

    mapping(address => uint256) private _stakes;
    uint8 private constant _decimals = 6;
    event Update(address indexed account, uint256 amount, uint256 stake);

    constructor() ERC20("TBYP Coin", "TBYP") {
        // Mint 100 tokens to msg.sender
        // Similar to how
        // 1 dollar = 100 cents
        // 1 token = 1 * (10 ** decimals)
        _mint(msg.sender, 104000 * 10**_decimals);
    }

    function addCredit(address account, uint256 amount) public onlyOwner{
        _mint(account, amount);
        _approve(account, owner(), balanceOf(account));
    }

    function totalBalanceOf(address account) public view virtual returns (uint256, uint256) {
            return (balanceOf(account), _stakes[account]);
        }

    function decimals() public view virtual override returns (uint8) {
        return _decimals;
    }

    function pay(address account, uint256 amount) public onlyOwner{
        require(amount <= balanceOf(account), "TBYPToken: cannot pay more than you own");
        _burn(account, amount);
    }

    function stake(address account, uint256 amount) public onlyOwner{
        require(amount <= balanceOf(account), "TBYPToken: cannot stake more than you own");
        _burn(account, amount);
        _stakes[account] += amount; 
    }

    function payAndStake(address account, uint256 amount, uint256 _stake) public onlyOwner{
        require(amount + _stake <= balanceOf(account), "TBYPToken: cannot pay and stake more than you own");
        _burn(account, amount);
        _stakes[account] += _stake; 
    }

    function unlockStake(address account, uint256 amount, uint256 reward) public onlyOwner{
        require(amount <= _stakes[account], "TBYPToken: cannot unlock more than you stake");
        _stakes[account] -= amount;
        _mint(account, amount + reward);
    }

    function _afterTokenTransfer(address from, address to, uint256 amount) internal virtual override{
        super._afterTokenTransfer(from, to, amount);
        emit Update(to, balanceOf(to), _stakes[to]);
    }

}


// 0x5B38Da6a701c568545dCfcB03FcB875f56beddC4
// 0xAb8483F64d9C6d1EcF9b849Ae677dD3315835cb2