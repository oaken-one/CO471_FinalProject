// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts-upgradeable/token/ERC20/ERC20Upgradeable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC20/extensions/ERC20BurnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC20/extensions/ERC20PausableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/access/OwnableUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/token/ERC20/extensions/ERC20PermitUpgradeable.sol";
import "@openzeppelin/contracts-upgradeable/proxy/utils/Initializable.sol";

contract TheFriendshipToken is Initializable, ERC20Upgradeable, ERC20BurnableUpgradeable, ERC20PausableUpgradeable, OwnableUpgradeable, ERC20PermitUpgradeable {
    /// @custom:oz-upgrades-unsafe-allow constructor
    constructor() {

        
    }

    // initializes contract for "TheFriendshipToken" 
    function initialize() initializer public {   
        __ERC20_init("TheFriendshipToken", "TFT");
        __ERC20Burnable_init();
        __ERC20Pausable_init();
        __Ownable_init(msg.sender);
        __ERC20Permit_init("TFT");
        }

    mapping (address => uint256) private _balances;


    // functions pause and unpause can start or stop the smart contract
    function pause() public onlyOwner {
        _pause();
    }

    function unpause() public onlyOwner {
        _unpause();
    }

    // functions to mint and burn tokens when someone's post to the Discord is upvoted or downvoted
    function mint(address to, uint256 amount) public onlyOwner {
        _balances[to] += amount;
    }

    function burn(address to, uint256 amount) public onlyOwner {
        require(_balances[to] >= amount);
        _balances[to] -= amount;
    }

    // functions to find the balance of an address or transfer tokens between addresses
    function balanceOf(address _owner) override public view returns (uint) { 
        return _balances[_owner];
    }

    function transfer(address _to, address _from, uint256 _value) public returns (bool) {
        require(_balances[_from] >= _value);
        _balances[_from] -= _value;
        _balances[_to] += _value;
        emit Transfer(_from, _to, _value);
        return true;
    }

    // The following functions are overrides required by Solidity.
    function _update(address from, address to, uint256 value)
        internal
        override(ERC20Upgradeable, ERC20PausableUpgradeable)
    {
        super._update(from, to, value);
    }
}
